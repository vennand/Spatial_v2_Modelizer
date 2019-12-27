# September 2019, code mutated by Andre Venne
# Modified version of Modelizer.py, code written by Valentin Allard
# Converts a .biomod or .s2mMod file to a Spacial_v2 format in matlab for casadi
#
#Segments have to be in order of dependencies (parent comes before child) in original file

import numpy as np
import math
import os


def coord_sys(axis):
    # define orthonormal coordinate system with given z-axis
    [a, b, c] = axis
    if a == 0:
        if b == 0:
            if c == 0:
                return [[1, 0, 0], [0, 1, 0], [0, 0, 1]], ''
            else:
                return [[1, 0, 0], [0, 1, 0], [0, 0, 1]], 'z'
        else:
            if c == 0:
                return [[1, 0, 0], [0, 1, 0], [0, 0, 1]], 'y'
            else:
                y_temp = [0, - c /b, 1]
    else:
        if b == 0:
            if c == 0:
                return [[1, 0, 0], [0, 1, 0], [0, 0, 1]], 'x'
            else:
                y_temp = [- c /a, 0, 1]
        else:
            y_temp = [- b /a, 1, 0]
    z_temp = [a, b, c]
    x_temp = np.cross(y_temp, z_temp)
    norm_x_temp = np.linalg.norm(x_temp)
    norm_z_temp = np.linalg.norm(z_temp)
    x = [1/norm_x_temp*x_el for x_el in x_temp]
    z = [1/norm_z_temp*z_el for z_el in z_temp]
    y = [y_el for y_el in np.cross(z, x)]
    return [x, y, z], ''


class OrthoMatrix:
    def __init__(self, translation=[0, 0, 0], rotation_1=[0, 0, 0], rotation_2=[0, 0, 0], rotation_3=[0, 0, 0]):
        self.trans = np.transpose(np.array([translation]))
        self.axe_1 = rotation_1  # axis of rotation for theta_1
        self.axe_2 = rotation_2  # axis of rotation for theta_2
        self.axe_3 = rotation_3  # axis of rotation for theta_3
        self.rot_1 = np.transpose(np.array(coord_sys(self.axe_1)[0]))  # rotation matrix for theta_1
        self.rot_2 = np.transpose(np.array(coord_sys(self.axe_2)[0]))  # rotation matrix for theta_2
        self.rot_3 = np.transpose(np.array(coord_sys(self.axe_3)[0]))  # rotation matrix for theta_3
        self.rotation_matrix = self.rot_3.dot(self.rot_2.dot(self.rot_1))  # rotation matrix for
        self.matrix = np.append(np.append(self.rotation_matrix, self.trans, axis=1), np.array([[0, 0, 0, 1]]), axis=0)

    def get_rotation_matrix(self):
        return self.rotation_matrix

    def set_rotation_matrix(self, rotation_matrix):
        self.rotation_matrix = rotation_matrix

    def get_translation(self):
        return self.trans

    def set_translation(self, trans):
        self.trans = trans

    def get_matrix(self):
        self.matrix = np.append(np.append(self.rotation_matrix, self.trans, axis=1), np.array([[0, 0, 0, 1]]), axis=0)
        return self.matrix

    def transpose(self):
        self.rotation_matrix = np.transpose(self.rotation_matrix)
        self.trans = -self.rotation_matrix.dot(self.trans)
        self.matrix = np.append(np.append(self.rotation_matrix, self.trans, axis=1), np.array([[0, 0, 0, 1]]), axis=0)
        return self.matrix

    def product(self, other):
        self.rotation_matrix = self.rotation_matrix.dot(other.get_rotation_matrix())
        self.trans = self.trans + other.get_translation()
        self.matrix = np.append(np.append(self.rotation_matrix, self.trans, axis=1), np.array([[0, 0, 0, 1]]), axis=0)

    def get_axis(self):
        return coord_sys(self.axe_1)[1] + coord_sys(self.axe_2)[1] + coord_sys(self.axe_3)[1]


def out_product(rotomatrix_1, rotomatrix_2):
    rotomatrix_prod = OrthoMatrix()
    rotomatrix_prod.set_translation(rotomatrix_1.get_translation() + rotomatrix_2.get_translation())
    rotomatrix_prod.set_rotation_matrix(rotomatrix_1.get_rotation_matrix().dot(rotomatrix_2.get_rotation_matrix()))
    rotomatrix_prod.get_matrix()
    return rotomatrix_prod


def get_words(_model):
    file = open(_model, "r")
    all_lines = file.readlines()
    all_words = []
    for line in all_lines:
        line = line[:-1]
        if line:
            if line.find('//') > -1:
                line = line[:line.find('//')]
            raw_line = line.split("\t")
            new_l = []
            for word in raw_line:
                if word != '':
                    for element in word.split(' '):
                        if element != '':
                            new_l.append(element)
            all_words.append(new_l)
    file.close()
    return all_words

def generate_Spatial_v2_values(_model):
    Spatial_v2_values = {}

    #42 degrés de liberté, 17 segments
    #Segment			Num	Parent	X	Y	Z
    #Bassin			S1	S0	q4	q5	q6
    #Thorax			S2	S1	−q7	q8	q9
    #Tête			S3	S2	−q10	q11	q12
    #Épaule droite		S4	S2	0	−q13	−q14
    #Bras droit			S5	S4	q15	−q16	−q17
    #Avant-bras droit		S6	S5	q18	0	−q19
    #Main droite		S7	S6	q20	−q21	0
    #Épaule gauche		S8	S2	0	q22	q23
    #Bras gauche		S9	S8	q24	q25	q26
    #Avant-bras gauche		S10	S9	q27	0	q28
    #Main gauche		S11	S10	q29	q30	0
    #Cuisse droite		S12	S1	q31	−q32	−q33
    #Jambe droite		S13	S12	−q34	0	0
    #Pied droit			S14	S13	q35	0	−q36
    #Cuisse gauche		S15	S1	q37	q38	q39
    #Jambe gauche		S16	S15	−q40	0	0
    #Pied gauche		S17	S16	q41	0	q42
    
    Spatial_v2_values['dof'] = {}
    Spatial_v2_values['dof']['Tz'] = '3'
    Spatial_v2_values['dof']['Somer'] = '4'
    Spatial_v2_values['dof']['Tilt'] = '5'
    Spatial_v2_values['dof']['Twist'] = '6'
    Spatial_v2_values['dof']['RighArmY'] = '8'
    Spatial_v2_values['dof']['LeftArmY'] = '10'
    
    Spatial_v2_values['NB'] = ''
    
    Spatial_v2_values['bodyN_name'] = ''
    Spatial_v2_values['jtype'] = ''
    Spatial_v2_values['parent'] = ''
    Spatial_v2_values['Xtree'] = ''
    Spatial_v2_values['I'] = ''
    
    Spatial_v2_values['markers'] = {}
    Spatial_v2_values['markers']['name'] = ''
    Spatial_v2_values['markers']['parent'] = ''
    Spatial_v2_values['markers']['coordinates'] = ''
    Spatial_v2_values['markers']['appearance'] = []
    
    bodyN_name_list = []
    jtype_list = []
    parent_dict = {}
    parent_list = []
    Xtree_list = []
    I_list = []
    markers_name_list = []
    markers_parent_list = []
    segment_dof = 0
    markers_coordinates_list = []
    markers_appearance_list = []
    marker_sum = 1
    
    for segment_num, segment in enumerate(_model.segments):
        segment_name = segment.name.lower()
        parent_dict[segment_name] = {}
        
        #For the root, assuming it is the first in the list
        if segment.dof_translation: #could be: if not segment.parent
            for dof_t in segment.dof_translation:
                bodyN_name_list.append('\'T' + dof_t + '_' + segment_name + '\'')
                segment_dof += 1
            for dof_r in segment.dof_rotation:
                bodyN_name_list.append('\'R' + dof_r + '_' + segment_name + '\'')
                segment_dof += 1
            
            jtype_list.append('\'R\'')
            parent_list.append('0')
            Xtree_list.append('eye(6)')
            
            I_list_matrix = []
            for row in segment.inertia:
                I_list_matrix.append(' '.join(row))
            I_list_temp = [segment.mass, '[' + ' '.join(segment.com) + ']', '[' + ';'.join(I_list_matrix) + ']']
            I_list_temp = 'mcI(' + ','.join(I_list_temp) + ')'
            I_list.append(I_list_temp)

            markers_appearance_list.append((str(segment_dof - 5), [str(number) for number in range(marker_sum, marker_sum+len(segment.markers))]))
            marker_sum += len(segment.markers)
            
        #For the other segments
        else:
            segment_parent = segment.parent.lower()
            #To give only to the first dof the RT matrix, and the others SX.eye(6)
            Xtree_bool = True
            for dof_r_num, dof_r in enumerate(segment.dof_rotation):
                bodyN_name_list.append('\'R' + dof_r + '_' + segment_name + '\'')
                jtype_list.append('\'R' + dof_r + '\'')

                if dof_r_num == 0:
                    parent_list.append(str(parent_dict[segment_parent]['segment_dof'] - 5))
                else:
                    parent_list.append(str(segment_dof - 5))

                if Xtree_bool:
                    Xtree_list_temp = []
                    for row in segment.rot_trans_matrix:
                        Xtree_list_temp.append(' '.join(row))
                    Xtree_list.append('inv(pluho([' + ';'.join(Xtree_list_temp) + ']))')
                    Xtree_bool = False
                else:
                    Xtree_list.append('eye(6)')

                #To give the inertia matrix and body appearance to the last degree of freedom of the segment
                if dof_r_num == len(segment.dof_rotation)-1:
                    I_list_matrix = []
                    for row in segment.inertia:
                        I_list_matrix.append(' '.join(row))
                    I_list_temp = [segment.mass, '[' + ' '.join(segment.com) + ']', '[' + ';'.join(I_list_matrix) + ']']
                    I_list_temp = 'mcI(' + ','.join(I_list_temp) + ')'
                    I_list.append(I_list_temp)

                    #Add +1 to segment_dof, because body counts doesn't start at 0
                    markers_appearance_list.append((str(segment_dof + 1 - 5), [str(number) for number in range(marker_sum, marker_sum+len(segment.markers))]))
                    marker_sum += len(segment.markers)
                else:
                    I_list_temp = 'zeros(6,6)'
                    I_list.append(I_list_temp)

                    markers_appearance_list.append((str(segment_dof + 1 - 5), []))
                
                segment_dof += 1
        
        #It is assumed that the segments in .biomod are in the same order as in the description of the 42 dof model
        parent_dict[segment_name]['segment_dof'] = segment_dof
        
        for marker in segment.markers:
            markers_name_list.append('\'' + marker.name + '\'')
            markers_parent_list.append(str(parent_dict[segment_name]['segment_dof']))
            markers_coordinates_list.append(' '.join(marker.position))
            #markers_appearance_dict[segment_num]['body'] =  # TODO

    Spatial_v2_values['NB'] = str(segment_dof - 6 + 1)
        
    Spatial_v2_values['bodyN_name'] = '{' + ','.join(bodyN_name_list) + '}'
    Spatial_v2_values['jtype'] = '{' + ','.join(jtype_list) + '}'

    Spatial_v2_values['parent'] = '[' + ','.join(parent_list) + ']'
    
    Spatial_v2_values['Xtree'] = '{' + ','.join(Xtree_list) + '}'
    
    Spatial_v2_values['I'] = '{' + ','.join(I_list) + '}'
    Spatial_v2_values['markers']['name'] = '{' + ','.join(markers_name_list) + '}'
    Spatial_v2_values['markers']['parent'] = '[' + ' '.join(markers_parent_list) + ']'
    Spatial_v2_values['markers']['coordinates'] = '[' + ';'.join(markers_coordinates_list) + ']\''
    Spatial_v2_values['markers']['appearance'] = markers_appearance_list
    
    
    
    return Spatial_v2_values


class Segment:
    def __init__(self, name, parent, rot_trans_matrix, dof_rotation, dof_translation, mass, inertia, com, rt_in_matrix):
        self.name = name
        self.parent = parent
        self.rot_trans_matrix = rot_trans_matrix
        self.dof_rotation = dof_rotation
        self.dof_translation = dof_translation
        self.mass = mass
        self.inertia = inertia
        self.com = com
        self.markers = []
        self.rt_in_matrix = rt_in_matrix

    def get_name(self):
        return self.name

    def set_name(self, new_name):
        self.name = new_name

    def get_parent(self):
        return self.parent

    def set_parent(self, new_parent):
        self.parent = new_parent
        return self.parent

    def get_rot_trans_matrix(self):
        return self.rot_trans_matrix

    def set_rot_trans_matrix(self, new_rot_trans_matrix):
        self.rot_trans_matrix = new_rot_trans_matrix
        return self.rot_trans_matrix

    def get_dof_rotation(self):
        return self.dof_rotation

    def set_dof_rotation(self, new_dof_rotation):
        self.dof_rotation = new_dof_rotation
        return self.dof_rotation

    def get_dof_translation(self):
        return self.dof_translation

    def set_dof_translation(self, new_dof_translation):
        self.dof_translation = new_dof_translation
        return self.dof_translation

    def get_mass(self):
        return self.mass

    def set_mass(self, new_mass):
        self.mass = new_mass
        return self.mass

    def get_inertia(self):
        return self.inertia

    def set_inertia(self, new_inertia):
        self.inertia = new_inertia
        return self.inertia

    def get_com(self):
        return self.com

    def set_com(self, new_com):
        self.com = new_com
        return self.com

    def get_rt_in_matrix(self):
        return self.rt_in_matrix

    def add_marker(self, marker):
        if type(marker) != Marker:
            assert 'wrong type of marker'
        elif marker.get_parent != self.name:
            assert 'this marker does not belong to this segment'
        self.markers.append(marker)

    def get_markers(self):
        return self.markers

    def set_marker(self, marker_to_be_set_index, changed_marker):
        if type(changed_marker) != Marker:
            assert 'wrong type of marker'
        self.markers[marker_to_be_set_index] = changed_marker

    def set_markers(self, list_of_markers):
        self.markers = []
        for element in list_of_markers:
            self.add_marker(element)
        return list_of_markers

    def get_relative_position(self):
        rot_trans_matrix = self.get_rot_trans_matrix()
        if self.get_rt_in_matrix() == 1:
            return [float(rot_trans_matrix[0][3]), float(rot_trans_matrix[1][3]), float(rot_trans_matrix[2][3])]
        elif self.get_rt_in_matrix() == 0:
            return [float(rot_trans_matrix[4]), float(rot_trans_matrix[5]), float(rot_trans_matrix[6])]

    def set_relative_position(self, new_relative_position):
        if len(new_relative_position) != 3:
            assert 'wrong size of vector to set new relative position of the segment'
        rot_trans_matrix = self.get_rot_trans_matrix()
        if self.get_rt_in_matrix() == 1:
            rot_trans_matrix[0][3] = str(new_relative_position[0])
            rot_trans_matrix[1][3] = str(new_relative_position[1])
            rot_trans_matrix[2][3] = str(new_relative_position[2])
            self.set_rot_trans_matrix(rot_trans_matrix)
        if self.get_rt_in_matrix() == 0:
            rot_trans_matrix[4] = str(new_relative_position[0])
            rot_trans_matrix[5] = str(new_relative_position[1])
            rot_trans_matrix[6] = str(new_relative_position[2])
            self.set_rot_trans_matrix(rot_trans_matrix)
        return rot_trans_matrix

    def length(self):
        relative_position = self.get_relative_position()
        return math.sqrt(relative_position[0]**2 + relative_position[1]**2 + relative_position[2]**2)

    def adjust_position(self, marker_index, adjust_factor):
        marker = self.get_markers()[marker_index]
        new_position = []
        for i in range(3):
            new_position.append(str(float(marker.get_position()[i])*adjust_factor))
        marker.set_position(new_position)
        self.set_marker(marker_index, marker)

    def set_length(self, new_segment_length, adjust_markers=True):
        length = self.length()
        relative_position = self.get_relative_position()
        adjust_factor = new_segment_length/length
        for i in range(3):
            relative_position[i] *= adjust_factor
        self.set_relative_position(relative_position)
        if adjust_markers:
            markers = self.get_markers()
            for marker_index in range(len(markers)):
                self.adjust_position(marker_index, adjust_factor)
        return relative_position


class Marker:
    def __init__(self, name, parent, position, technical):
        self.name = name
        self.parent = parent
        self.position = position
        self.technical = technical

    def get_name(self):
        return self.name

    def set_name(self, new_name):
        self.name = new_name
        return self.name

    def get_parent(self):
        return self.parent

    def set_parent(self, new_parent):
        self.parent = new_parent
        return self.parent

    def get_position(self):
        return self.position

    def set_position(self, new_position):
        self.position = new_position
        return self.position

    def get_technical(self):
        return self.technical

    def set_technical(self, new_technical):
        self.technical = new_technical
        return self.technical


class MuscleGroup:
    def __init__(self, name, origin_parent, insertion_parent):
        self.name = name
        self.origin_parent = origin_parent
        self.insertion_parent = insertion_parent
        self.muscles = []

    def get_name(self):
        return self.name

    def set_name(self, new_name):
        self.name = new_name
        return self.name

    def get_origin_parent(self):
        return self.origin_parent

    def set_origin_parent(self, new_origin_parent):
        self.origin_parent = new_origin_parent
        return self.origin_parent

    def get_insertion_parent(self):
        return self.insertion_parent

    def set_insertion_parent(self, new_insertion_parent):
        self.insertion_parent = new_insertion_parent
        return self.insertion_parent

    def add_muscle(self, muscle):
        if type(muscle) != Muscle:
            assert 'wrong type of muscle'
        if muscle.get_muscle_group() != self.name:
            assert 'this muscle does not belong to this muscle group'
        self.muscles.append(muscle)
        return self.muscles

    def remove_muscle(self, muscle_index):
        return self.muscles.pop(muscle_index)

    def get_muscles(self):
        return self.muscles

    def set_muscles(self, list_of_muscles):
        self.muscles = []
        for element in list_of_muscles:
            self.add_muscle(element)
        return list_of_muscles

    def set_muscle(self, muscle_index, modified_muscle):
        if type(modified_muscle) != Muscle:
            assert 'wrong type of muscle'
        if modified_muscle.get_muscle_group() != self.name:
            assert 'this muscle does not belong to this muscle group'
        self.muscles[muscle_index] = modified_muscle
        return self.muscles[muscle_index]


class Muscle:
    def __init__(self, name, _type, state_type, muscle_group, origin_position, insertion_position, optimal_length,
                 maximal_force, tendon_slack_length, pennation_angle, max_velocity):
        self.name = name
        self._type = _type
        self.state_type = state_type
        self.muscle_group = muscle_group
        self.origin_position = origin_position
        self.insertion_position = insertion_position
        self.optimal_length = optimal_length
        self.maximal_force = maximal_force
        self.tendon_slack_length = tendon_slack_length
        self.pennation_angle = pennation_angle
        self.max_velocity = max_velocity
        self.pathpoints = []

    def get_name(self):
        return self.name

    def set_name(self, new_name):
        self.name = new_name
        return self.name

    def get_type(self):
        return self._type

    def set_type(self, new_type):
        self._type = new_type
        return self._type

    def get_state_type(self):
        return self.state_type

    def set_state_type(self, new_state_type):
        self.state_type = new_state_type
        return self.state_type

    def get_muscle_group(self):
        return self.muscle_group

    def set_muscle_group(self, new_muscle_group):
        self.muscle_group = new_muscle_group
        return self.muscle_group

    def get_origin_position(self):
        return self.origin_position

    def set_origin_position(self, new_origin_position):
        self.origin_position = new_origin_position
        return self.origin_position

    def get_insertion_position(self):
        return self.insertion_position

    def set_insertion_position(self, new_insertion_position):
        self.insertion_position = new_insertion_position
        return self.insertion_position

    def get_optimal_length(self):
        return self.optimal_length

    def set_optimal_length(self, new_optimal_length):
        self.optimal_length = new_optimal_length
        return self.optimal_length

    def get_maximal_force(self):
        return self.maximal_force

    def set_maximal_force(self, new_maximal_force):
        self.maximal_force = new_maximal_force
        return self.maximal_force

    def get_tendon_slack_length(self):
        return self.tendon_slack_length

    def set_tendon_slack_length(self, new_tendon_slack_length):
        self.tendon_slack_length = new_tendon_slack_length
        return self.tendon_slack_length

    def get_pennation_angle(self):
        return self.pennation_angle

    def set_pennation_angle(self, new_pennation_angle):
        self.pennation_angle = new_pennation_angle
        return self.pennation_angle

    def get_max_velocity(self):
        return self.max_velocity

    def set_max_velocity(self, new_max_velocity):
        self.max_velocity = new_max_velocity
        return self.max_velocity

    def get_pathpoints(self):
        return self.pathpoints

    def add_pathpoint(self, pathpoint):
        if type(pathpoint) != Pathpoint:
            assert 'wrong type of pathpoint'
        self.pathpoints.append(pathpoint)

    def set_pathpoint(self, pathpoint_to_be_set_index, changed_pathpoint):
        if type(changed_pathpoint) != Pathpoint:
            assert 'wrong type of pathpoint'
        self.pathpoints[pathpoint_to_be_set_index] = changed_pathpoint

    def set_pathpoints(self, list_of_pathpoints):
        self.pathpoints = []
        for element in list_of_pathpoints:
            self.add_pathpoint(element)
        return list_of_pathpoints

    def set_pathpoint(self, pathpoint_index, modified_pathpoint):
        if type(modified_pathpoint) != Pathpoint:
            assert 'wrong type of pathpoint'
        self.pathpoints[pathpoint_index] = modified_pathpoint
        return self.pathpoints[pathpoint_index]


class Pathpoint:
    def __init__(self, name, parent, muscle, muscle_group, position):
        self.name = name
        self.parent = parent
        self.muscle = muscle
        self.muscle_group = muscle_group
        self.position = position

    def get_name(self):
        return self.name

    def set_name(self, new_name):
        self.name = new_name
        return self.name

    def get_parent(self):
        return self.parent

    def set_parent(self, new_parent):
        self.parent = new_parent
        return self.parent

    def get_muscle(self):
        return self.muscle

    def set_muscle(self, new_muscle):
        self.muscle = new_muscle
        return self.muscle

    def get_muscle_group(self):
        return self.muscle_group

    def set_muscle_group(self, new_muscle_group):
        self.muscle_group = new_muscle_group
        return self.muscle_group

    def get_position(self):
        return self.position

    def set_position(self, new_position):
        self.position = new_position
        return self.position


class BiorbdModel:
    def __init__(self, path=None):
        self.segments = []
        self.markers = []
        self.muscle_groups = []
        self.muscles = []
        self.pathpoints = []
        self.path = path
        self.write_path = ''
        self.file = ''
        self.words = ''
        self.version = '3'
        self.root_actuated = '0'
        self.external_forces = '0'
        # TODO handle biorbd version differences

    def read(self, path=None):
        if not path:
            if self.path:
                self.words = get_words(self.path)
            else:
                assert "You need to give a file to read"
        else:
            self.words = get_words(path)
            self.path = path
        number_line = 0

        name_segment = ''
        parent_segment = ''
        rot_trans_matrix = []
        dof_translation = ''
        dof_rotation = ''
        mass = ''
        inertia = [[], [], []]
        com = []
        rt_in_matrix = 1

        name_marker = ''
        parent_marker = ''
        position_marker = []
        technical = ''

        muscle_group_name = ''
        muscle_group_origin_parent = ''
        muscle_group_insertion_parent = ''

        muscle_name = ''
        muscle_type = ''
        muscle_state_type = ''
        muscle_group = ''
        origin_position = []
        insertion_position = []
        optimal_length = ''
        maximal_force = ''
        tendon_slack_length = ''
        pennation_angle = ''
        max_velocity = ''

        pathpoint_name = ''
        pathpoint_parent = ''
        pathpoint_muscle = ''
        pathpoint_muscle_group = ''
        pathpoint_position = []

        is_segment = False
        is_marker = False
        is_muscle_group = False
        is_muscle = False
        is_viapoint = False

        while number_line < len(self.words):
            line = self.words[number_line]
            if not line:
                number_line += 1
                continue
            if line[0] == 'version':
                self.version = line[1]
                number_line += 1
                continue
            if line[0] == 'root_actuated':
                self.root_actuated = line[1]
                number_line += 1
                continue
            if line[0] == 'external_forces':
                self.external_forces = line[1]
                number_line += 1
                continue
            if line[0] == 'segment':
                name_segment = line[1]
                number_line += 1
                is_segment = True
                continue
            if line[0] == 'parent' and is_segment:
                parent_segment = line[1]
                number_line += 1
                continue
            if line[0] == 'RT' and is_segment:
                if len(line) == 1:
                    rt_in_matrix = 1
                    rot_trans_matrix = [[], [], [], []]
                    rot_trans_matrix[0] = self.words[number_line + 1]
                    rot_trans_matrix[1] = self.words[number_line + 2]
                    rot_trans_matrix[2] = self.words[number_line + 3]
                    rot_trans_matrix[3] = self.words[number_line + 4]
                    number_line += 5
                    continue
                if len(line) == 8:
                    rt_in_matrix = 0
                    for i in range(7):
                        rot_trans_matrix.append(line[i+1])
                    number_line += 1
                    continue

            if line[0] == 'translations' and is_segment:
                dof_translation = line[1]
                number_line += 1
                continue
            if line[0] == 'rotations' and is_segment:
                dof_rotation = line[1]
                number_line += 1
                continue
            if line[0] == 'mass' and is_segment:
                mass = line[1]
                number_line += 1
                continue
            if line[0] == 'inertia' and is_segment:
                inertia[0] = self.words[number_line + 1]
                inertia[1] = self.words[number_line + 2]
                inertia[2] = self.words[number_line + 3]
                number_line += 4
                continue
            if line[0] == 'com' and is_segment:
                com.append(line[1])
                com.append(line[2])
                com.append(line[3])
                number_line += 1
                continue
            if line[0] == 'endsegment' and is_segment:
                new_segment = Segment(name_segment, parent_segment, rot_trans_matrix, dof_rotation, dof_translation,
                                      mass, inertia, com, rt_in_matrix)
                if new_segment not in self.segments:
                    self.segments.append(new_segment)
                number_line += 1
                is_segment = False
                name_segment = ''
                parent_segment = ''
                rot_trans_matrix = []
                dof_translation = ''
                dof_rotation = ''
                mass = 0
                inertia = [[], [], []]
                com = []
                continue
            if line[0] == 'marker':
                name_marker = line[1]
                is_marker = True
                number_line += 1
                continue
            if line[0] == 'parent' and is_marker:
                parent_marker = line[1]
                number_line += 1
                continue
            if line[0] == 'position' and is_marker:
                position_marker.append(line[1])
                position_marker.append(line[2])
                position_marker.append(line[3])
                number_line += 1
                continue
            if line[0].find('technical') != -1 and is_marker:
                technical = line[1]
                number_line += 1
                continue
            if line[0] == 'endmarker' and is_marker:
                new_marker = Marker(name_marker, parent_marker, position_marker, technical)
                if new_marker not in self.markers:
                    self.markers.append(new_marker)
                    self.segments[-1].add_marker(self.markers[-1])
                is_marker = False
                number_line += 1
                name_marker = ''
                parent_marker = ''
                position_marker = []
                technical = ''
                continue
            if line[0] == 'musclegroup' and not is_muscle and not is_viapoint:
                muscle_group_name = line[1]
                is_muscle_group = True
                number_line += 1
                continue
            if line[0] == 'OriginParent' and is_muscle_group:
                muscle_group_origin_parent = line[1]
                number_line += 1
                continue
            if line[0] == 'InsertionParent' and is_muscle_group:
                muscle_group_insertion_parent = line[1]
                number_line += 1
                continue
            if line[0] == 'endmusclegroup' and is_muscle_group:
                new_muscle_group = MuscleGroup(muscle_group_name, muscle_group_origin_parent,
                                               muscle_group_insertion_parent)
                if new_muscle_group not in self.muscle_groups:
                    self.muscle_groups.append(new_muscle_group)
                is_muscle_group = False
                number_line += 1
                muscle_group_name = ''
                muscle_group_origin_parent = ''
                muscle_group_insertion_parent = ''
                continue

            if line[0] == 'muscle' and not is_viapoint:
                muscle_name = line[1]
                is_muscle = True
                number_line += 1
                continue
            if line[0] == 'Type' and is_muscle:
                muscle_type = line[1]
                number_line += 1
                continue
            if line[0] == 'statetype' and is_muscle:
                muscle_state_type = line[1]
                number_line += 1
                continue
            if line[0] == 'musclegroup' and is_muscle:
                muscle_group = line[1]
                number_line += 1
                continue
            if line[0] == 'OriginPosition' and is_muscle:
                origin_position.append(line[1])
                origin_position.append(line[2])
                origin_position.append(line[3])
                number_line += 1
                continue
            if line[0] == 'InsertionPosition' and is_muscle:
                insertion_position.append(line[1])
                insertion_position.append(line[2])
                insertion_position.append(line[3])
                number_line += 1
                continue
            if line[0] == 'optimalLength' and is_muscle:
                optimal_length = line[1]
                number_line += 1
                continue
            if line[0] == 'maximalForce' and is_muscle:
                maximal_force = line[1]
                number_line += 1
                continue
            if line[0] == 'tendonSlackLength' and is_muscle:
                tendon_slack_length = line[1]
                number_line += 1
                continue
            if line[0] == 'pennationAngle' and is_muscle:
                pennation_angle = line[1]
                number_line += 1
                continue
            if line[0] == 'maxVelocity' and is_muscle:
                max_velocity = line[1]
                number_line += 1
                continue
            if line[0] == 'endmuscle' and is_muscle:
                new_muscle = Muscle(muscle_name, muscle_type, muscle_state_type, muscle_group, origin_position,
                                    insertion_position, optimal_length, maximal_force, tendon_slack_length,
                                    pennation_angle, max_velocity)
                if new_muscle not in self.muscles:
                    self.muscles.append(new_muscle)
                    self.muscle_groups[-1].add_muscle(self.muscles[-1])
                is_muscle = False
                muscle_name = ''
                muscle_type = ''
                muscle_state_type = ''
                muscle_group = ''
                origin_position = []
                insertion_position = []
                optimal_length = ''
                maximal_force = ''
                tendon_slack_length = ''
                pennation_angle = ''
                max_velocity = ''
                number_line += 1
                continue

            if line[0] == 'viapoint':
                pathpoint_name = line[1]
                is_viapoint = True
                number_line += 1
                continue
            if line[0] == 'parent' and is_viapoint:
                pathpoint_parent = line[1]
                number_line += 1
                continue
            if line[0] == 'muscle' and is_viapoint:
                pathpoint_muscle = line[1]
                number_line += 1
                continue
            if line[0] == 'musclegroup' and is_viapoint:
                pathpoint_muscle_group = line[1]
                number_line += 1
                continue
            if line[0] == 'position' and is_viapoint:
                pathpoint_position.append(line[1])
                pathpoint_position.append(line[2])
                pathpoint_position.append(line[3])
                number_line += 1
                continue
            if line[0] == 'endviapoint' and is_viapoint:
                new_pathpoint = Pathpoint(pathpoint_name, pathpoint_parent, pathpoint_muscle, pathpoint_muscle_group,
                                          pathpoint_position)
                if new_pathpoint not in self.pathpoints:
                    self.pathpoints.append(new_pathpoint)
                    self.muscles[-1].add_pathpoint(self.pathpoints[-1])
                is_viapoint = False
                pathpoint_name = ''
                pathpoint_parent = ''
                pathpoint_muscle = ''
                pathpoint_muscle_group = ''
                pathpoint_position = []
                number_line += 1
                continue
            else:
                number_line += 1
                continue

    # TODO complete this section
    # Up to: appearance
    def write(self, write_path=None):
        if not write_path:
            if self.write_path:
                self.file = open(self.write_path, "w")
            elif self.path:
                self.write_path = os.path.splitext(self.path)[0]+'_Spatial_v2.m'
                self.file = open(self.write_path, "w")
            else:
                assert "Weird, this shouldn't happen! ERR001"
        else:
            self.write_path = write_path
            self.file = open(self.write_path, "w")
        
        model = generate_Spatial_v2_values(self)

        self.file.write('function [model, data] = GenerateModel(data)\n')
        self.file.write('% version ' + self.version + '\n')
        self.file.write('\n')
        self.file.write('% File extracted from ' + self.path + '\n')
        self.file.write('\n')
        self.file.write('% Informations générales\n'
                   '% root_actuated\t' + self.root_actuated + '\n'
                   '% external_forces\t' + self.external_forces + '\n')
        self.file.write('\n')
        self.file.write('import casadi.*' + '\n')
        self.file.write('\n')
        # To modify
        self.file.write('model.name = \'' + os.path.splitext(self.path)[0] + '\';\n'
                        '\n'
                        'model.NB = ' + model['NB'] + ';\n'
                        '\n'
                        'model.bodyN_name = ' + model['bodyN_name'] + ';\n'
                        'model.jtype = ' + model['jtype'] + ';\n'
                        'model.parent = ' + model['parent'] + ';\n'
                        '\n'
                        'model.Xtree = ' + model['Xtree'] + ';\n'
                        'model.I = ' + model['I'] + ';\n'
                        '\n'
                        'model.markers.name = ' + model['markers']['name'] + ';\n'
                        '\n'
                        'model.markers.parent = ' + model['markers']['parent'] + ';\n'
                        'model.markers.coordinates = ' + model['markers']['coordinates'] + ';\n'
                        '\n'
                        'model.appearance.base = { \'line\', [1.1 0 0; 0 0 0; 0 1.1 0; 0 0 0; 0 0 1.1]};\n'
                        '\n'
                        )
        # Appearance of markers in showmotion (function of spatial_v2)
        for body, markers in model['markers']['appearance']:
            if markers:
                sphere = []
                for marker in markers:
                    sphere.append('\'sphere\', model.markers.coordinates(:, ' + marker + '), 0.01')
                self.file.write('model.appearance.body{' + body + '} = {' + ','.join(sphere) + '};\n')
            else:
                self.file.write('model.appearance.body{' + body + '} = {};' + '\n')

        self.file.write('model = floatbase(model);\n'
                        '\n'
                        'model.nq = model.NB;\n'
                        'model.nx = model.nq+model.nq;\n'
                        'model.nu = model.nq-6;\n'
                        '\n'
                        'data.x0 = zeros(model.nx,1);\n'
                        'data.u0 = zeros(model.nu,1);\n'
                        '\n'
                        'model.idx_q = 1:model.nq;\n'
                        'model.idx_v = model.nq+1:2*model.nq;\n'
                        '\n'
                        'xmin_base = [-inf,-inf,-inf,-inf,-inf,-inf];\n'
                        'xmax_base = [ inf, inf, inf, inf, inf, inf];\n'
                        '\n'
                        'model.xmin = [xmin_base\'; -inf*ones(model.nq-6,1); xmin_base\'; -100*ones(model.nq-6,1)];\n'
                        'model.xmax = [xmax_base\';  inf*ones(model.nq-6,1); xmax_base\';  100*ones(model.nq-6,1)];\n'
                        '\n'
                        'model.umin = -50*ones(model.nu,1);\n'
                        'model.umax =  50*ones(model.nu,1);\n'
                        '\n'
                        '% model.gravity = [0 0 0];\n'
                        )
        self.file.write('end\n')
        self.file.close()
        return 0

    def get_segments(self):
        return self.segments

    def get_muscle_groups(self):
        return self.muscle_groups

    def set_segment(self, segment_index, modified_segment):
        if type(modified_segment) == Segment:
            self.segments[segment_index] = modified_segment
        else:
            assert "wrong type of modified segment"
        return modified_segment

    def add_muscle_group(self, new_muscle_group):
        if type(new_muscle_group) != MuscleGroup:
            assert 'wrong type of muscle group'
        self.muscle_groups.append(new_muscle_group)
        return new_muscle_group

    def remove_muscle_group(self, muscle_group_index):
        return self.muscle_groups.pop(muscle_group_index)

    def add_muscle(self, muscle_group_index, new_muscle):
        return self.muscle_groups[muscle_group_index].add_muscle(new_muscle)

    def remove_muscle(self, muscle_group_index, muscle_index):
        return self.muscle_groups[muscle_group_index].remove_muscle(muscle_index)

    def add_pathpoint(self, muscle_group_index, muscle_index, new_pathpoint):
        muscle = self.muscle_groups[muscle_group_index].get_muscles()[muscle_index]
        muscle.add_pathpoint(new_pathpoint)
        return self.muscle_groups[muscle_group_index].set_muscle(muscle_index, muscle)

    def remove_pathpoint(self, muscle_group_index, muscle_index, pathpoint_index):
        muscle = self.muscle_groups[muscle_group_index].get_muscles()[muscle_index]
        muscle.remove_pathpoint(pathpoint_index)
        return self.muscle_groups[muscle_group_index].set_muscle(muscle_index, muscle)

    def get_number_of_muscle_groups(self):
        return len(self.muscle_groups)

    def get_total_muscle_number(self):
        res = 0
        for muscle_group in self.muscle_groups:
            res += len(muscle_group.get_muscles())
        return res

    def add_segment(self, new_segment):
        if type(new_segment) != Segment:
            assert 'wrong type of segment'
        self.segments.append(new_segment)
        return new_segment

    def remove_segment(self, segment_index):
        return self.segments.pop(segment_index)

    def get_number_of_segments(self):
        return len(self.segments)

    def get_segment(self, segment_index):
        return self.segments[segment_index]

    def get_segment_index(self, segment_name):
        index = 0
        for segment in self.get_segments():
            if segment.get_name() == segment_name:
                return index
            else:
                index += 1
        else:
            return None


def main():
    model = BiorbdModel()
    model.read('DoCi.s2mMod')

    model.write('GenerateModel.m')

    return 0


if __name__ == "__main__":
    main()


