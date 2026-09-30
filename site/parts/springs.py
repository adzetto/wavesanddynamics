"""The site's springs: generated, do not edit (tools/motion_springs.mjs).

Motion 12.43.0, spring(visual duration, bounce 0) for each of the site's
travel durations. Each entry is (visual ms, settle ms, CSS linear() easing):
the motion is where it is going at the visual duration and still at the
settle one, so a transition runs for the settle time and anything timed off
it (a delay, a visibility flip) keeps the visual one.
"""

MOTION = "12.43.0"
SPRINGS = {
    "quick": (120, 250, "linear(0, 0.4615, 0.8176, 0.9471, 0.9858, 0.9964, 0.9991, 1)"),
    "fast": (160, 350, "linear(0, 0.2794, 0.6159, 0.8186, 0.9198, 0.966, 0.986, 0.9943, 0.9977, 0.9991, 0.9997, 1)"),
    "mid": (240, 500, "linear(0, 0.1495, 0.3955, 0.6061, 0.7562, 0.8542, 0.9148, 0.9512, 0.9724, 0.9846, 0.9914, 0.9953, 0.9974, 0.9986, 0.9992, 1, 1)"),
    "draw": (360, 700, "linear(0, 0.0791, 0.2369, 0.4041, 0.5522, 0.6723, 0.7649, 0.8339, 0.884, 0.9198, 0.945, 0.9625, 0.9746, 0.9829, 0.9885, 0.9923, 0.9949, 0.9966, 0.9977, 0.9985, 0.999, 1, 1)"),
    "slow": (420, 800, "linear(0, 0.0572, 0.1795, 0.3195, 0.4536, 0.5713, 0.6695, 0.7486, 0.8109, 0.859, 0.8956, 0.9232, 0.9439, 0.9591, 0.9704, 0.9786, 0.9846, 0.9889, 0.9921, 0.9943, 0.996, 0.9971, 0.998, 0.9986, 0.999, 1, 1)"),
}

