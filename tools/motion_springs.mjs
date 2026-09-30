// The site's springs, from Motion's own spring() (https://motion.dev, MIT).
//
// Things that travel on the site (a rail scaling in, an arrow's head sliding,
// a line drawing itself, a panel opening) move on a physical spring, not on a
// cubic-bezier: Motion's AI kit ("prefer physics-based springs for physical
// motion"), and a serious site, so no overshoot (bounce 0). Colour and
// opacity keep their curves (--ease-state, --ease): a spring means nothing
// for a colour.
//
// Each spring is named for the duration token it stands in for: its visual
// duration IS that token (120ms, 160ms, 240ms, 360ms, 420ms), and Motion
// returns the longer time the spring takes to settle, with the curve sampled
// as a CSS linear() easing.
//
// Run from a folder where `npm i motion@12` has been run (the site itself
// is not a Node project):
//   node <repo>/tools/motion_springs.mjs > <repo>/site/parts/springs.py
import { createRequire } from "node:module"
import { pathToFileURL } from "node:url"

const require = createRequire(pathToFileURL(process.cwd() + "/"))
const { spring } = require("motion")
const version = require("motion/package.json").version

const TOKENS = [["quick", 0.12], ["fast", 0.16], ["mid", 0.24], ["draw", 0.36], ["slow", 0.42]]
const lines = TOKENS.map(([name, visual]) => {
    const css = String(spring(visual, 0))          // "<settle>ms linear(...)"
    const [, ms, easing] = /^(\d+)ms (linear\(.*\))$/.exec(css)
    return `    "${name}": (${Math.round(visual * 1000)}, ${ms}, "${easing}"),`
})

console.log(`"""The site's springs: generated, do not edit (tools/motion_springs.mjs).

Motion ${version}, spring(visual duration, bounce 0) for each of the site's
travel durations. Each entry is (visual ms, settle ms, CSS linear() easing):
the motion is where it is going at the visual duration and still at the
settle one, so a transition runs for the settle time and anything timed off
it (a delay, a visibility flip) keeps the visual one.
"""

MOTION = "${version}"
SPRINGS = {
${lines.join("\n")}
}
`)
