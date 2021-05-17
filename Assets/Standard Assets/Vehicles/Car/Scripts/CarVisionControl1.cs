using System;
using System.Text;
using System.Collections.Generic;
using UnityEngine;
using UnityStandardAssets.CrossPlatformInput;

using System.Globalization;

using HybridWebSocket;

public class JsonResponse
{
    public float vert_shift;
    public int stop;
    public int car;
    public int stopId;
    public int carId;
    // public DetectionObject objects;
}

public class DetectionObject
{
    public ObjectProps stop;
    public ObjectProps car;
}

public class ObjectProps
{
    public int area;
    public int conf_area;
}

namespace UnityStandardAssets.Vehicles.Car
{
    [RequireComponent(typeof (CarController))]
    public class CarVisionControl1 : MonoBehaviour
    {
        public CarController m_Car; // the car controller we want to use
        public Camera Camera;

        float h = 0.5f, v = 0f;

        WebSocket ws;
        PID carSpeedZero = new PID(0.1f, 0f, 0.02f);
        PID carSpeedStatic = new PID(0.1f, 0f, 0.02f);
        PID carSpeedControlledByObject = new PID(0.1f, 0f, 0.02f);
        float speed = 0f;
        float zeroPidSpeed = 0f;
        float forwardPidSpeed = 0f;
        float objectPidSpeed = 0f;

        int objectArea = 0;

        int lastStopId = -1;

        Animator animator;
        bool isStopped = false;
        bool isFollowing = false;
        bool gonnaStop = false;

        void Start () {

            ws.Send(Encoding.ASCII.GetBytes("start"));
            // InvokeRepeating("Capture", 1f, 0.2f);  //1s delay, repeat every 1s

        }

        private void PrintSpeed() {
            Debug.Log(m_Car.CurrentSpeed);
        }

        private void Awake()
        {
            
            ws = WebSocketFactory.CreateInstance("ws://localhost:12345");

            // Connect to the server
            ws.Connect();
            // get the car controller
            m_Car = GetComponent<CarController>();
            animator = GetComponent<Animator>();


            ws.OnMessage += (byte[] msg) =>
            {
                Debug.Log("WS received message: " + Encoding.UTF8.GetString(msg));

                var response = JsonUtility.FromJson<JsonResponse>(Encoding.UTF8.GetString(msg));

                h = response.vert_shift;
                v = (0.5 - Math.Abs(0.5 - h)) < 0.43f ? 0f : 0.05f;
                // v = (0.5 - Math.Abs(0.5 - h)) < 0.43f ? 0f : forwardPidSpeed / (1f / 0.5f);
                
                if (isFollowing) {
                    if (isStopped) {
                        v = zeroPidSpeed;
                    } else {
                        if (response.stopId > lastStopId && response.stop > 0 && response.stop < 1000) {
                            // v = -0.07f * response.stop / 1000;
                            gonnaStop = true;

                            lastStopId = response.stopId;
                            v = zeroPidSpeed;

                        } else if (response.stop >= 1000) {
                            // v = 0.05f;
                        }
                        if (response.car > 0 && response.car < 3000) {
                            v = objectPidSpeed;
                            objectArea = response.car;
                        }
                        if (speed < 0) {
                            v = forwardPidSpeed;
                        }
                    }
                }
                
                Debug.Log(v + " " + speed + " " + forwardPidSpeed + " " + response.car + " " + response.stopId + " " + isStopped + " " + objectArea + " " + objectPidSpeed);
            };

            // Add OnClose event listener
            ws.OnClose += (WebSocketCloseCode code) =>
            {
                Debug.Log("WS closed with code: " + code.ToString());
            };
        }

        private void OnDestroy() {
            ws.Close();
        }


        private void FixedUpdate()
        {
            isStopped = animator.GetBool("isStopped");
            isFollowing = animator.GetBool("isFollowing");
            if (gonnaStop) {
                SetStopped(animator, true);
                gonnaStop = false;
            }
            speed = m_Car.CurrentSpeed;

            var velocity = m_Car.GetComponent<Rigidbody>().velocity;
            var localVel = transform.InverseTransformDirection(velocity);
            
            if (localVel.z > 0)
            {
                // We're moving forward
            }
            else
            {
                // We're moving backward
                if (speed > 0) speed = -speed;
            }

            zeroPidSpeed = (float)carSpeedZero.calc(speed, 0f);
            forwardPidSpeed = (float)carSpeedStatic.calc(speed, 10f);
            objectPidSpeed = (float)(carSpeedControlledByObject.calc(objectArea, 800)) / 800;

            m_Car.Move(h * 2 - 1, v, v, 0f);
        }

        public void SetStopped(Animator animator, bool value) {
            animator.SetBool("isStopped", value);
        }
    
        public void Capture()
        {
            RenderTexture activeRenderTexture = RenderTexture.active;
            RenderTexture.active = Camera.targetTexture;
    
            Camera.Render();
    
            Texture2D image = new Texture2D(Camera.targetTexture.width, Camera.targetTexture.height);
            image.ReadPixels(new Rect(0, 0, Camera.targetTexture.width, Camera.targetTexture.height), 0, 0);
            image.Apply();
            RenderTexture.active = activeRenderTexture;
    
            byte[] bytes = image.EncodeToPNG();
            Destroy(image);


            ws.Send(bytes);
        }
    }
}

public class PID {
	
	private double P;
	private double I;
	private double D;
	
	private double prevErr;
	private double sumErr;
	
	public PID (double P, double I, double D) {
		this.P = P;
		this.I = I;
		this.D = D;
	}
	
	public double calc (double current, double target) {
		
		double dt = Time.fixedDeltaTime;
		
		double err = target - current;
		this.sumErr += err;
		
		double force = this.P * err + this.I * this.sumErr * dt + this.D * (err - this.prevErr) / dt;
		
		this.prevErr = err;
		return force;
	}
	
};