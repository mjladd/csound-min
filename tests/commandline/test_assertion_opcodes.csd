<CsTest>
description = "assert_true and assert_false pass under --run-unit-tests"

[expect]
exit = 0
</CsTest>
<CsoundSynthesizer>
<CsOptions>
-n -d -m0 --run-unit-tests
</CsOptions>
<CsInstruments>
sr=44100
ksmps=1
nchnls=1
instr 1
  i1 = 1 + 1
  assert_true(i1 == 2)
  assert_false(i1 == 3)
endin
</CsInstruments>
<CsScore>
i1 0 0
e
</CsScore>
</CsoundSynthesizer>
