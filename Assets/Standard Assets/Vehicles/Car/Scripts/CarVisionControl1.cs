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
    public DetectionObject objects;
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
        private CarController m_Car; // the car controller we want to use
        public Camera Camera;

        float h = 0.5f, v = 0f;

        WebSocket ws;
        PID carSpeed = new PID(100, 0, 20);

        void Start () {

            ws.Send(Encoding.ASCII.GetBytes("start"));
            // InvokeRepeating("Capture", 1f, 0.2f);  //1s delay, repeat every 1s

        }

        private void Awake()
        {
            
            ws = WebSocketFactory.CreateInstance("ws://localhost:12345");

            ws.OnMessage += (byte[] msg) =>
            {
                // Debug.Log("WS received message: " + Encoding.UTF8.GetString(msg));

                var response = JsonUtility.FromJson<JsonResponse>(Encoding.UTF8.GetString(msg));

                h = response.vert_shift;
                // h = float.Parse(Encoding.UTF8.GetString(msg), CultureInfo.InvariantCulture.NumberFormat);
                // v = Convert.ToSingle(Math.Max(0, (0.5 - Math.Abs(0.5 - h))) / 5);
                v = (0.5 - Math.Abs(0.5 - h)) < 0.43f ? 0f : 0.05f;

                if (response.stop > 0 && response.stop < 1000) {
                    // v = -0.03f * response.stop / 1000;
                    // v = (float)carSpeed.calc(m_Car.CurrentSpeed, 0f);
                } else if (response.stop > 0 && response.stop >= 1000) {

                }
                
                // Debug.Log(m_Car.CurrentSpeed);
                // Debug.Log(m_Car.GetComponent<Rigidbody>().velocity.magnitude.ToString());
                // v = (0.5 - Math.Abs(0.5 - h)) < 0.43f ? -0.05f : 0.05f;
                // v = Math.Max(0, (0.5 - Math.Abs(0.5 - h))) < 0.43f ? -0.05f : 0.05f;
                // v = Math.Max(0, (0.5 - Math.Abs(0.5 - h))) < 0.47f ? -0.05f : 0.05f;

                Debug.Log(h.ToString() + " " + (h * 2 - 1) + " " + v);

                // Debug.Log(h.ToString() + " " + (h * 2 - 1) + " " + v + " " + response.objects.stop.area.ToString());

                // 0 = 1
                // 1 = -1
            };

            // Add OnClose event listener
            ws.OnClose += (WebSocketCloseCode code) =>
            {
                Debug.Log("WS closed with code: " + code.ToString());
            };

            // Connect to the server
            ws.Connect();
            // get the car controller
            m_Car = GetComponent<CarController>();   
        }

        private void OnDestroy() {
            ws.Close();
        }


        private void FixedUpdate()
        {
            m_Car.Move(h * 2 - 1, v, v, 0f);
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