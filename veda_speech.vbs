Set Sapi = Wscript.CreateObject("SAPI.SpVoice")
Sapi.Rate = 1
Sapi.Volume = 100
Sapi.Speak Wscript.Arguments(0)