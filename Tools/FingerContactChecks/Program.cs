using VRSharp.Core;
static void Check(bool ok,string name) { if(!ok) throw new Exception(name); }
float r=2;
Check(VRSharpMathHelper.StepFingerContactTarget(.7f,.7f,.79f*r,r,1f/90)<.7f,"deep contact opens");
Check(VRSharpMathHelper.StepFingerContactTarget(.7f,.7f,.8f*r,r,1f/90)==.7f,"0.8 radius holds");
Check(VRSharpMathHelper.StepFingerContactTarget(.7f,.7f,r,r,1f/90)==.7f,"edge contact holds");
Check(VRSharpMathHelper.StepFingerContactTarget(.7f,.7f,1.01f*r,r,1f/90)>.7f,"separation recloses");
Check(VRSharpMathHelper.StepFingerContactTarget(.7f,.7f,0,r,1f/90)<.7f,"inside collision opens");
Check(VRSharpMathHelper.StepFingerContactTarget(.7f,1,.4f*r,r,1f/90)<.7f,"opening immediately cancels queued closure");
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

foreach(float weight in new[]{-1f,0f,.5f,1f,2f,float.NaN,float.PositiveInfinity,float.NegativeInfinity}) {
 float expected=float.IsFinite(weight)?Math.Clamp(weight,0,1):0;
 Check(VRSharpMathHelper.NormalizePoseWeight(weight)==expected,"authored pose normalization");
}
Console.WriteLine("Authored pose weight boundaries passed.");

Check(VRSharpMathHelper.BlendPoseWeight(.2f,.8f,0)==.2f,"trigger starts at base");
Check(VRSharpMathHelper.BlendPoseWeight(.2f,.8f,1)==.8f,"trigger ends at authored endpoint");
Check(Math.Abs(VRSharpMathHelper.BlendPoseWeight(.2f,.8f,.5f)-.5f)<1e-6,"trigger midpoint");
Check(VRSharpMathHelper.BlendPoseWeight(0,1,-1)==0,"negative trigger clamps");
Check(VRSharpMathHelper.BlendPoseWeight(0,1,2)==1,"high trigger clamps");
Check(VRSharpMathHelper.BlendPoseWeight(float.NaN,1,float.NaN)==0,"invalid blend remains finite");
Console.WriteLine("Authored trigger blend boundaries passed.");
