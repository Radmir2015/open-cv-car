
# public class PID {
	
# 	private double P;
# 	private double I;
# 	private double D;
	
# 	private double prevErr;
# 	private double sumErr;
	
# 	public PID (double P, double I, double D) {
# 		this.P = P;
# 		this.I = I;
# 		this.D = D;
# 	}
	
# 	public double calc (double current, double target) {
		
# 		double dt = Time.fixedDeltaTime;
		
# 		double err = target - current;
# 		this.sumErr += err;
		
# 		double force = this.P * err + this.I * this.sumErr * dt + this.D * (err - this.prevErr) / dt;
		
# 		this.prevErr = err;
# 		return force;
# 	}
	
# };

class PID():
    def __init__(self, p, i, d):
        self.p = p
        self.i = i
        self.d = d
        self.prevErr = 0
        self.sumErr = 0
    
    def calc(self, time, current, target):
        err = target - current
        self.sumErr += err

        force = self.p * err + self.i * self.sumErr * time + self.d * (err - self.prevErr) / time

        self.prevErr = err
        return force

p = PID(100, 0, 20)
print(p.calc(1, 0.05, 0))
print(p.calc(2, 0.04, 0))