"""Run the actual counter function with a deterministic animation clock."""
import subprocess
import unittest

from build_report import SCRIPT


class MetricAnimationTest(unittest.TestCase):
    def test_counter_progress_completion_restart_and_reduced_motion(self):
        function = SCRIPT.split('function animateMetrics(view){', 1)[1].split('\nfunction animate(view)', 1)[0]
        subprocess.run(['node', '-'], input=r'''
const assert=require('node:assert/strict');
let time=0, next=0, reduced=false;
const frames=new Map();
const performance={now:()=>time};
function requestAnimationFrame(fn){frames.set(++next,fn);return next}
function cancelAnimationFrame(id){frames.delete(id)}
function motionAllowed(){return !reduced}
function advance(ms){time+=ms;const pending=[...frames.values()];frames.clear();pending.forEach(fn=>fn(time))}
const nodes=['82.40%','88.70%','67.70%','3'].map(textContent=>({textContent,dataset:{}}));
const expected=nodes.map(n=>n.textContent);
const view={hidden:false,querySelectorAll:()=>nodes};
''' + 'function animateMetrics(view){' + function + r'''
animateMetrics(view);
assert.deepEqual(nodes.map(n=>n.textContent),['0.00%','0.00%','0.00%','0']);
advance(400);
assert(parseFloat(nodes[0].textContent)>0 && parseFloat(nodes[0].textContent)<82.4);
assert.match(nodes[0].textContent,/^\d+\.\d{2}%$/);
animateMetrics(view); // Interrupt without losing the original targets.
assert.equal(frames.size,4);
advance(1000);
assert.deepEqual(nodes.map(n=>n.textContent),expected);
assert.equal(frames.size,0);
animateMetrics(view);advance(200);view.hidden=true;advance(16);
assert.deepEqual(nodes.map(n=>n.textContent),expected);
assert.equal(frames.size,0);
view.hidden=false;reduced=true;animateMetrics(view);
assert.deepEqual(nodes.map(n=>n.textContent),expected);
assert.equal(frames.size,0);
reduced=false;animateMetrics(view);advance(100);reduced=true;advance(16);
assert.deepEqual(nodes.map(n=>n.textContent),expected);
assert.equal(frames.size,0);
''', text=True, check=True)


if __name__ == '__main__':
    unittest.main()
