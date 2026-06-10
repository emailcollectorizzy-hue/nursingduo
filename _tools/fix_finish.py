# Restore finishSectionLesson (consumed by the phase2 block replace), adapted:
# sd-replay re-renders the scroll doc instead of calling the old pager.
import io

p = r"C:\Users\izzyp\.claude\skills\quizpage\template-v2.html"
snap = r"C:\Users\izzyp\.claude\skills\quizpage\template-v2.pre-pulse.html"
s = io.open(p, encoding="utf-8").read()
assert "function finishSectionLesson" not in s, "already present"

orig = io.open(snap, encoding="utf-8").read()
a = orig.index("function finishSectionLesson() {")
b = orig.index("// Keyboard nav for the study lesson")
fn = orig[a:b].rstrip() + "\n\n"

# adapt the replay handler to the scrollytelling renderer
old_replay = 'document.getElementById("sd-replay").addEventListener("click", () => { state.lessonStep = state.lessonStep || {}; state.lessonStep[s.id] = 0; saveState(); setLessonStep(0); });'
new_replay = 'document.getElementById("sd-replay").addEventListener("click", () => { state.lessonStep = state.lessonStep || {}; state.lessonStep[s.id] = 0; lessonIdx = 0; saveState(); renderCurrentSection(); window.scrollTo(0, 0); });'
assert old_replay in fn
fn = fn.replace(old_replay, new_replay)

marker = "// Keyboard nav for the study lesson — ArrowRight: next chunk"
assert marker in s
s = s.replace(marker, fn + marker)
io.open(p, "w", encoding="utf-8", newline="\n").write(s)
print("finishSectionLesson restored,", fn.count(chr(10)), "lines")
