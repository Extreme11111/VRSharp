using VRSharp.Core;
foreach (float sample in new[] {-2f,0f,.5f,1f,2f,float.NaN,float.PositiveInfinity,float.NegativeInfinity})
foreach (float previous in new[] {-1f,0f,.7f,2f,float.NaN,float.PositiveInfinity,float.NegativeInfinity}) {
 float actual=FingerInput.Normalize(sample,previous);
 if(!float.IsFinite(actual)||actual<0||actual>1) throw new Exception("finite bounded input");
 if(float.IsFinite(sample)&&actual!=Math.Clamp(sample,0,1)) throw new Exception("finite sample");
 if(!float.IsFinite(sample)&&float.IsFinite(previous)&&actual!=Math.Clamp(previous,0,1)) throw new Exception("retain prior input");
}
// Stateful adapter stream: malformed samples must retain the most recent accepted target.
float target = 0;
foreach (float sample in new[] { .25f, float.NaN, .75f, float.PositiveInfinity, -1f, float.NegativeInfinity, 2f })
{
 float before = target;
 target = FingerInput.Normalize(sample, target);
 if (!float.IsFinite(sample) && target != before) throw new Exception("invalid stream sample changed target");
}
if (target != 1f) throw new Exception("last valid sample wins");
foreach (float invalid in new[] {float.NaN,float.PositiveInfinity,float.NegativeInfinity})
 if (FingerInput.Normalize(invalid,invalid)!=0f) throw new Exception("invalid initial state recovers open");
Console.WriteLine("Finger input: 56 boundary combinations, malformed input stream and recovery passed.");
