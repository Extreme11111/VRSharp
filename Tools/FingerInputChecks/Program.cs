using VRSharp.Core;
foreach (float sample in new[] {-2f,0f,.5f,1f,2f,float.NaN,float.PositiveInfinity,float.NegativeInfinity})
foreach (float previous in new[] {-1f,0f,.7f,2f,float.NaN}) {
 float actual=FingerInput.Normalize(sample,previous);
 if(!float.IsFinite(actual)||actual<0||actual>1) throw new Exception("finite bounded input");
 if(float.IsFinite(sample)&&actual!=Math.Clamp(sample,0,1)) throw new Exception("finite sample");
 if(!float.IsFinite(sample)&&float.IsFinite(previous)&&actual!=Math.Clamp(previous,0,1)) throw new Exception("retain prior input");
}
Console.WriteLine("Finger input: 40 boundary combinations passed.");
