using VRSharp.Core;
static void Check(bool condition, string message) { if (!condition) throw new Exception(message); }
int cases = 0;
for (int flags = 0; flags < 16; flags++)
foreach (bool left in new[] { false, true })
foreach (int count in new[] { 0, 1, 2 })
foreach (bool existing in new[] { false, true })
{
    bool disabled = (flags & 1) != 0, dl = (flags & 2) != 0,
        dr = (flags & 4) != 0, single = (flags & 8) != 0;
    bool allowed = GrabAdmission.Allows(disabled, dl, dr, single, left, count, existing);
    if (disabled) Check(!allowed, "global disable wins over ownership");
    else if ((left && dl) || (!left && dr)) Check(!allowed, "selected hand disabled");
    else if (single && count > 0 && !existing) Check(!allowed, "exclusive occupied");
    else Check(allowed, "eligible hand admitted");
    cases++;
}
Check(GrabAdmission.Allows(false,false,false,true,true,0,false), "first hand");
Check(!GrabAdmission.Allows(false,false,false,true,false,1,false), "second hand rejected");
Check(GrabAdmission.Allows(false,false,false,true,false,0,false), "release frees ownership");
Console.WriteLine($"Grab admission: {cases} policy combinations and ownership sequence passed.");
