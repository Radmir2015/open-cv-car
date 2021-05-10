using WebSocketSharp;
using UnityEngine;

public class Ws : MonoBehaviour {

    // Use this for initialization
    WebSocket ws;

    void Start () {

        // Create WebSocket instance
        ws = new WebSocket("ws://localhost:12345");

        // Add OnOpen event listener
        // ws.OnOpen += () =>
        // {
        //     Debug.Log("WS connected!");
        //     Debug.Log("WS state: " + ws.GetState().ToString());

        //     ws.Send(Encoding.UTF8.GetBytes("Hello from Unity 3D!"));
        // };

        // Add OnMessage event listener
        ws.OnMessage += (sender, e) =>
        { // Encoding.UTF8.GetString(
            Debug.Log("WS received message: " + e.Data);

            // ws.Close();
        };

        // Add OnError event listener
        // ws.OnError += (string errMsg) =>
        // {
        //     Debug.Log("WS error: " + errMsg);
        // };

        // // Add OnClose event listener
        // ws.OnClose += (WebSocketCloseCode code) =>
        // {
        //     Debug.Log("WS closed with code: " + code.ToString());
        // };

        // Connect to the server
        ws.Connect();

    }
    
    // Update is called once per frame
    void Update () {
        
    }
}