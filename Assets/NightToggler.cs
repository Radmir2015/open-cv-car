using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEditor;

public class NightToggler : MonoBehaviour
{
    public List<GameObject> CarLights;
    public Light DirectionalLight;
    // Start is called before the first frame update

    int cx = 0;

    void Start()
    {
        
    }

    // Update is called once per frame
    void Update()
    {
        if (Input.GetKeyDown(KeyCode.Q)) {
            DirectionalLight.transform.Rotate((cx++ % 2 == 0 ? -1 : 1) * 55, 0, 0);
            // Lightmapping.Bake();
        }

        if (Input.GetKeyDown(KeyCode.R)) {
            DirectionalLight.transform.Rotate((cx++ % 2 == 0 ? -1 : 1) * 180, 0, 0);
            // Lightmapping.Bake();
        }

        if (Input.GetKeyDown(KeyCode.E)) {
            foreach (var cl in CarLights) { cl.SetActive(!cl.activeSelf); }
        }
    }
}
