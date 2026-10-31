using VRSharp.Core;
static void Check(bool ok,string name) { if(!ok) throw new Exception(name); }
float r=2;
Check(VRSharpMathHelper.StepFingerContactTarget(.7f,.7f,.79f*r,r,1f/90)<.7f,"deep contact opens");
Check(VRSharpMathHelper.StepFingerContactTarget(.7f,.7f,.8f*r,r,1f/90)==.7f,"0.8 radius holds");
Check(VRSharpMathHelper.StepFingerContactTarget(.7f,.7f,r,r,1f/90)==.7f,"edge contact holds");
Check(VRSharpMathHelper.StepFingerContactTarget(.7f,.7f,1.01f*r,r,1f/90)>.7f,"separation recloses");
Check(VRSharpMathHelper.StepFingerContactTarget(.7f,.7f,0,r,1f/90)<.7f,"inside collision opens");
Check(VRSharpMathHelper.StepFingerContactTarget(.7f,1,.4f*r,r,1f/90)<.7f,"opening immediately cancels queued closure");
// Invalid observations hold a usable pose; +infinity is the no-contact sentinel.
foreach (float invalid in new[] { float.NaN, float.NegativeInfinity })
 Check(VRSharpMathHelper.StepFingerContactTarget(.7f,1f,invalid,r,1f/90)==.7f,"invalid distance holds current pose");
Check(VRSharpMathHelper.StepFingerContactTarget(.7f,.7f,float.PositiveInfinity,r,1f/90)>.7f,"no-contact sentinel recloses");
foreach (float invalid in new[] { 0f, -1f, float.NaN, float.PositiveInfinity, float.NegativeInfinity }) {
 Check(VRSharpMathHelper.StepFingerContactTarget(.7f,.4f,0,r,invalid)==.4f,"invalid timestep preserves target");
 Check(VRSharpMathHelper.StepFingerContactTarget(.7f,.4f,0,invalid,1f/90)==.4f,"invalid radius preserves target");
}
foreach (float invalid in new[] { float.NaN, float.PositiveInfinity, float.NegativeInfinity }) {
 Check(VRSharpMathHelper.StepFingerContactTarget(invalid,.6f,r,r,1f/90)==.6f,"invalid current recovers from target");
 Check(VRSharpMathHelper.StepFingerContactTarget(.6f,invalid,r,r,1f/90)==.6f,"invalid target recovers from current");
 Check(VRSharpMathHelper.StepFingerContactTarget(invalid,invalid,r,r,1f/90)==0,"both invalid recover open");
 Check(VRSharpMathHelper.StepFingerContactTarget(invalid,invalid,0,r,0)==0,"invalid timestep still returns finite pose");
}
Check(VRSharpMathHelper.StepFingerContactTarget(-1,2,r,r,1f/90)==0,"current lower bound");
Check(VRSharpMathHelper.StepFingerContactTarget(2,-1,r,r,1f/90)==1,"current upper bound");
Check(VRSharpMathHelper.StepFingerContactTarget(.7f,.7f,-1,r,1f/90)==VRSharpMathHelper.StepFingerContactTarget(.7f,.7f,0,r,1f/90),"finite negative penetration clamps to zero");
foreach(int fps in new[]{30,60,90,120})
foreach(float initial in new[]{0f,1f}) {
 float current=initial,target=initial,dt=1f/fps,min=1,max=0;
 for(int i=0;i<fps*5;i++) {
  // Model a fingertip moving into a plane as closure increases.
  target=VRSharpMathHelper.StepFingerContactTarget(current,target,(1.2f-current)*r,r,dt);
  current=float.Lerp(current,target,1-MathF.Exp(-24*dt));
  Check(float.IsFinite(current)&&current>=0&&current<=1,"finite bounded pose");
  if(i>fps*4){min=Math.Min(min,current);max=Math.Max(max,current);}
 }
 float ratio=1.2f-current;
 Check(ratio>=.798f&&ratio<=1.015f,"settles in contact band");
 Check(max-min<.002f,"no persistent oscillation");
 Console.WriteLine($"{fps} Hz, initial {initial}: final={current:F5}, distance/R={ratio:F5}, tail swing={max-min:F6}");
}
Console.WriteLine("Finger contact production helper: all checks passed");
