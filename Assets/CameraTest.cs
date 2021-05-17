using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class CameraTest : MonoBehaviour
{
    // Start is called before the first frame update
    public Camera camera;
    void Start()
    {
        Debug.Log(camera.focalLength);
    }

    // Update is called once per frame
    void Update()
    {
        
    }
}
