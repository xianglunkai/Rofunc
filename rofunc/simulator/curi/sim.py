import math

import numpy as np
from isaacgym import gymapi
from isaacgym import gymutil
from rofunc.simulator.base.base_sim import init_sim, init_env, init_attractor


def update_robot(traj, gym, envs, attractor_handles, axes_geom, sphere_geom, viewer, num_envs, index, t):
    gym.clear_lines(viewer)
    for i in range(num_envs):
        # Update attractor target from current franka state
        attractor_properties = gym.get_attractor_properties(envs[i], attractor_handles[i])
        pose = attractor_properties.target
        # pose.p: (x, y, z), pose.r: (w, x, y, z)
        # pose.p.x = 0.2 * math.sin(1.5 * t - math.pi * float(i) / num_envs)
        # pose.p.y = 0.7 + 0.1 * math.cos(2.5 * t - math.pi * float(i) / num_envs)
        # pose.p.z = 0.2 * math.cos(1.5 * t - math.pi * float(i) / num_envs)
        pose.p.x = 0.7 + traj[index, 0] * 2
        pose.p.y = 0.2 + traj[index, 2] * 0.5
        pose.p.z = traj[index, 1] * 0.5

        # pose.p.y = -0.2 + 0.2 * math.sin(1.5 * t - math.pi * float(i) / num_envs) + 1
        # pose.p.x = 0.7 + 0.2 * math.cos(1.5 * t - math.pi * float(i) / num_envs) + 0.1
        # pose.p.z = 0.5

        gym.set_attractor_target(envs[i], attractor_handles[i], pose)

        # Draw axes and sphere at attractor location
        gymutil.draw_lines(axes_geom, gym, viewer, envs[i], pose)
        gymutil.draw_lines(sphere_geom, gym, viewer, envs[i], pose)


def show(args):
    # Initial gym and sim
    gym, sim_params, sim, viewer = init_sim(args)

    # Load CURI asset and set the env
    asset_root = "../assets"
    asset_file = "urdf/curi/urdf/curi_isaacgym.urdf"
    init_env(gym, sim, viewer, asset_root, asset_file, num_envs=5, spacing=3.0, fix_base_link=False)

    while not gym.query_viewer_has_closed(viewer):
        # Step the physics
        gym.simulate(sim)
        gym.fetch_results(sim, True)

        # Step rendering
        gym.step_graphics(sim)
        gym.draw_viewer(viewer, sim, False)
        gym.sync_frame_time(sim)


def run_traj(args, traj):
    # Initial gym and sim
    gym, sim_params, sim, viewer = init_sim(args)

    # Load CURI asset and set the env
    asset_root = "../assets"
    asset_file = "urdf/curi/urdf/curi_isaacgym.urdf"
    envs, curi_handles = init_env(gym, sim, viewer, asset_root, asset_file, num_envs=1, fix_base_link=False)

    # Create the attractor
    attracted_joint = "panda_right_hand"
    attractor_handles, axes_geom, sphere_geom = init_attractor(gym, envs, viewer, curi_handles, attracted_joint)

    # get joint limits and ranges for Franka
    curi_dof_props = gym.get_actor_dof_properties(envs[0], curi_handles[0])
    curi_lower_limits = curi_dof_props['lower']
    curi_upper_limits = curi_dof_props['upper']
    curi_mids = 0.5 * (curi_upper_limits + curi_lower_limits)
    curi_num_dofs = len(curi_dof_props)

    for i in range(len(envs)):
        # Set updated stiffness and damping properties
        gym.set_actor_dof_properties(envs[i], curi_handles[i], curi_dof_props)

        # Set ranka pose so that each joint is in the middle of its actuation range
        curi_dof_states = gym.get_actor_dof_states(envs[i], curi_handles[i], gymapi.STATE_NONE)
        for j in range(curi_num_dofs):
            curi_dof_states['pos'][j] = curi_mids[j]
        gym.set_actor_dof_states(envs[i], curi_handles[i], curi_dof_states, gymapi.STATE_POS)

    # Time to wait in seconds before moving robot
    next_curi_update_time = 2

    index = 0
    while not gym.query_viewer_has_closed(viewer):
        # Every 0.01 seconds the pose of the attactor is updated
        t = gym.get_sim_time(sim)
        if t >= next_curi_update_time:
            update_robot(traj, gym, envs, attractor_handles, axes_geom, sphere_geom, viewer, len(envs), index, t)
            next_curi_update_time += 0.01
            index += 1
            if index >= len(traj):
                index = 0

        # Step the physics
        gym.simulate(sim)
        gym.fetch_results(sim, True)

        # Step rendering
        gym.step_graphics(sim)
        gym.draw_viewer(viewer, sim, False)
        gym.sync_frame_time(sim)

    print("Done")

    gym.destroy_viewer(viewer)
    gym.destroy_sim(sim)


if __name__ == '__main__':
    args = gymutil.parse_arguments(description="CURI Attractor Example")

    traj = np.load('/home/ubuntu/Data/2022_09_09_Taichi/rep3_l.npy')
    run_traj(args, traj)
    # show(args)

    # import rofunc as rf
    #
    # gym, sim_params, sim, viewer = rf.franka.init_sim(args)
    # envs, curi_handles = rf.franka.init_env(gym, sim, viewer)
    # attractor_handles, axes_geom, sphere_geom = rf.franka.init_attractor(gym, envs, viewer, curi_handles)
    # run_traj(None, gym, sim, envs, viewer, curi_handles, attractor_handles, axes_geom, sphere_geom)
