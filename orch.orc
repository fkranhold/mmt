sr     = 44100
nchnls = 1
0dbfs  = 100

; Calculates the frequency for a given number of half steps,
; relative to a given root note.
; p4: Volume    (0 to 100, note that multiple voices add up)
; p5: Frequency (e.g. 261.625 for equally-tempered C4)
instr 1
  iFreq = p5
  iAmp  = p4
  kEnv madsr .05, .3, .9, .1
  aOut oscil iAmp, iFreq
  out kEnv*aOut
endin
