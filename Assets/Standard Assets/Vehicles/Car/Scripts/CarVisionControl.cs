using System;
using System.Text;
using UnityEngine;
using UnityStandardAssets.CrossPlatformInput;

using System.Globalization;

using HybridWebSocket;

namespace UnityStandardAssets.Vehicles.Car
{
    [RequireComponent(typeof (CarController))]
    public class CarVisionControl : MonoBehaviour
    {
        private CarController m_Car; // the car controller we want to use
        public Camera Camera;

        float h = 0.5f, v = 0f;

        WebSocket ws;

        void Start () {

            ws = WebSocketFactory.CreateInstance("ws://localhost:12345");

            ws.OnMessage += (byte[] msg) =>
            {
                Debug.Log("WS received message: " + Encoding.UTF8.GetString(msg));

                h = float.Parse(Encoding.UTF8.GetString(msg), CultureInfo.InvariantCulture.NumberFormat);
                // v = Convert.ToSingle((0.5 - Math.Abs(0.5 - h)) / 5);
                v = (0.5 - Math.Abs(0.5 - h)) < 0.43f ? -0.05f : 0.05f;

                Debug.Log(h * 2 - 1 + " " + v);

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

            InvokeRepeating("Capture", 1f, 0.2f);  //1s delay, repeat every 1s

        }

        private void Awake()
        {
            // get the car controller
            m_Car = GetComponent<CarController>();
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
