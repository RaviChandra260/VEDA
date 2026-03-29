Set Sapi = Wscript.CreateObject("SAPI.SpVoice")
Sapi.Rate = 1
Sapi.Speak Wscript.Arguments(0)