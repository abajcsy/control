'''
Copyright (C) 2015 Travis DeWolf

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import controllers.target_list as target_list
import controllers.forcefield as forcefield

import numpy as np

def get_line_traj(start, goal, num_waypoints):
	(sx, sy) = start
	(gx, gy) = goal
	traj_x = [None]*num_waypoints
	traj_y = [None]*num_waypoints
	
	dist_x = gx-sx
	dist_y = gy-sy	
	
	traj_x[0] = sx
	traj_y[0] = sy
	for i in range(1,num_waypoints):
		traj_x[i] = traj_x[i-1]+dist_x/(num_waypoints-1)
		traj_y[i] = traj_y[i-1]+dist_y/(num_waypoints-1)
	return (traj_x, traj_y)

def Task(arm, controller_class, x_bias=0., y_bias=2., dist=.4, 
         force=None, write_to_file=False, sequence=None, **kwargs):
	"""
	This task sets up the arm to reach to 8 targets center out from
	(x_bias, y_bias) at a distance=dist.
	"""

	# check controller type ------------------
	controller_name = controller_class.__name__.split('.')[1]
	if controller_name not in ('ilqr', 'lqr', 'osc', 'gradient_approximation', 'ahf'):
		raise Exception('Cannot perform reaching task with this controller.')

	# set arm specific parameters ------------
	if arm.DOF == 2:
		dist = .075
		kp = 20 # position error gain on the PD controller
		threshold = .05 
		y_bias = .35
	elif arm.DOF == 3:
		kp = 100 
		threshold = .02
	else:
		raise Exception('Cannot perform reaching task with this arm.')

	# generate the path to follow -------------
	# set up the reaching trajectories, 8 points around unit circle
	#targets_x = [dist * np.cos(theta) + x_bias \
	#	            for theta in np.linspace(0, np.pi*2, 9)][:-1]
	#targets_y = [dist * np.sin(theta) + y_bias \
	#	            for theta in np.linspace(0, np.pi*2, 9)][:-1]
	#trajectory = np.ones((3*len(targets_x)+3, 2))*np.nan

	#start = 0 if sequence is None else int(sequence)
	#for ii in range(start,len(targets_x)): 
	#	trajectory[ii*3+1] = [0, y_bias]
	#	trajectory[ii*3+2] = [targets_x[ii], targets_y[ii]]
	#trajectory[-2] = [0, y_bias]

	num_waypoints = 2
	(traj_x, traj_y) = get_line_traj((-0.4, 0.0), (0.2,0.5), num_waypoints)

	start = 0 if sequence is None else int(sequence)
	trajectory = np.ones((num_waypoints+2, 2))*np.nan

	for ii in range(num_waypoints): 
		trajectory[ii+1] = [traj_x[ii], traj_y[ii]]

	print "trajectory: "
	print trajectory

	# generate control shell -----------------
	additions = []
	if force is not None:
		print('applying joint velocity based forcefield...')
		additions.append(forcefield.Addition(scale=force))
		task = 'arm%i/forcefield'%arm.DOF

	controller = controller_class.Control(
		            additions=additions,
		            kp=kp,
		            kv=np.sqrt(kp),
		            task='arm%i/reach'%arm.DOF,
		            write_to_file=write_to_file)

	control_pars = {'target_list':trajectory,
		            'threshold':threshold, 'pen_down':True} # how close to get to each target}
	control_shell = target_list.Shell(controller=controller, **control_pars)

	# generate runner parameters -----------
	runner_pars = {'infinite_trail':True, 
		           'title':'Task: Reaching',
		           'trajectory':trajectory}

	return (control_shell, runner_pars)
