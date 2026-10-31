using System.Text.Json;
using UnrealSharp.CoreUObject;
using VRSharp.Core;

static void Require(bool valid, string message)
{
    if (!valid) throw new Exception(message);
}

var rows = new List<object>();
foreach (int fps in new[] { 15, 30, 60, 72, 90, 120, 144, 240 })
{
    double h = 1.0 / fps;
    int n = (int)Math.Ceiling(h * 120 - 1e-8);
    float k = 427.199127f, d = 41.337593f;
    double kp = VRSharpMathHelper.ComputeSpringAcceleration(new(1, 0, 0), default, k, d, (float)h).X;
    double kd = VRSharpMathHelper.ComputeSpringAcceleration(default, new(1, 0, 0), k, d, (float)h).X;
    double trace = 2 - kp * h * h - kd * h;
    double determinant = 1 - kd * h;
    Require(Math.Abs(determinant - Math.Exp(-d * h)) < 1e-6, $"Pole determinant at {fps} Hz");
    Require(Math.Abs(trace - 2 * Math.Exp(-d * h / 2)) < 1e-6, $"Pole decay at {fps} Hz");
    var trajectories = new List<double[]>();
    foreach (double mass in new[] { 0.2, 0.45, 2, 5, 20 })
    {
        double x = 0, v = 0, maximum = 0, settled = 0;
        var samples = new List<double>();
        for (int frame = 0; frame < fps * 2; ++frame)
        {
            double a = VRSharpMathHelper.ComputeSpringAcceleration(new(10 - x, 0, 0), new(-v, 0, 0), k, d, (float)h).X;
            double impulse = mass * a * h;
            v += impulse / mass;
            for (int step = 0; step < n; ++step)
            {
                x += v * h / n;
            }
            Require(double.IsFinite(x) && double.IsFinite(v), "Finite response");
            maximum = Math.Max(maximum, x);
            if (x < 9.5) settled = (frame + 1) * h;
            samples.Add(x);
        }
        Require(Math.Abs(x - 10) < 1e-5, "Converges to target");
        Require(maximum <= 10.0001, "Critical response must not overshoot");
        trajectories.Add(samples.ToArray());
        if (mass == 0.45) rows.Add(new { fps, mass, settle95Seconds = settled + h, overshootCm = Math.Max(maximum - 10, 0) });
    }
    foreach (var trajectory in trajectories)
        Require(trajectory.Zip(trajectories[0]).All(p => Math.Abs(p.First - p.Second) < 1e-10), "Mass independent force response");
}

// Large gain + abruptly changing frame steps exposes errors hidden by fixed-FPS tests.
foreach (float k in new[] { 1f, 427.199127f, 10000f, 1e6f, 1e10f })
{
    double x = 0, v = 0;
    for (int frame = 0; frame < 500; ++frame)
    {
        double h = frame % 2 == 0 ? 1.0 / 15 : 1.0 / 120;
        int n = frame % 2 == 0 ? 8 : 1;
        double a = VRSharpMathHelper.ComputeSpringAcceleration(new(1 - x, 0, 0), new(-v, 0, 0), k, 2 * MathF.Sqrt(k), (float)h).X;
        v += a * h;
        for (int step = 0; step < n; ++step)
        {
            x += v * h / n;
        }
        Require(double.IsFinite(x) && Math.Abs(x) < 100, $"Variable-step stability with k={k}");
    }
}

foreach (double angle in new[] { 1e-12, 1e-5, 0.5, Math.PI })
{
    var q = new FQuat(Math.Sin(angle / 2), 0, 0, Math.Cos(angle / 2));
    var a = VRSharpMathHelper.RotationVector(q, new(0, 0, 0, 1));
    var b = VRSharpMathHelper.RotationVector(new(-q.X, -q.Y, -q.Z, -q.W), new(0, 0, 0, 1));
    Require((a - b).LengthSquared() < 1e-20, "Quaternion double-cover invariant");
    Require(Math.Abs(a.X - angle) < 1e-10, "Small-angle axis accuracy");
}
var halfTurnA = VRSharpMathHelper.RotationVector(new(1, 0, 0, 0), new(0, 0, 0, 1));
var halfTurnB = VRSharpMathHelper.RotationVector(new(-1, 0, 0, -0.0), new(0, 0, 0, 1));
Require((halfTurnA - halfTurnB).LengthSquared() < 1e-20, "Exact half-turn signed zero");
using var tuning = JsonDocument.Parse(File.ReadAllText(Path.Combine(AppContext.BaseDirectory, "Fixtures", "HandSpring-Tuning-20261017.json")));
foreach (var hand in tuning.RootElement.GetProperty("hands").EnumerateArray())
{
    var settings = hand.GetProperty("settings");
    double mass = hand.GetProperty("old_runtime_mass").GetDouble();
    double inertia = hand.GetProperty("old_reference_inertia").GetDouble();
    double linearGain = VRSharpMathHelper.ComputeSpringAcceleration(new(1, 0, 0), default,
        settings.GetProperty("LocationStiffness").GetSingle(), settings.GetProperty("LocationDamping").GetSingle(), 1f / 120).X;
    double angularGain = VRSharpMathHelper.ComputeSpringAcceleration(new(1, 0, 0), default,
        settings.GetProperty("RotationStiffness").GetSingle(), settings.GetProperty("RotationDamping").GetSingle(), 1f / 120).X;
    Require(Math.Abs(linearGain * mass - 2000) < 0.001, "Matches old 120 Hz initial position response");
    Require(Math.Abs(angularGain * inertia - 8000) < 0.003, "Matches old 120 Hz initial rotation response on calibration axis");
}
Console.WriteLine(JsonSerializer.Serialize(new { passed = true, rows }, new JsonSerializerOptions { WriteIndented = true }));
