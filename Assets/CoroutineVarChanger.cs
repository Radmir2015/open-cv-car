using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class CoroutineVarChanger : MonoBehaviour {
    public void DoStop(Animator anim) {
        StartCoroutine(WaitAndChangeStop(anim));
    }

    public void DoFollow(Animator anim) {
        StartCoroutine(WaitAndChangeFollowing(anim));
    }

    IEnumerator WaitAndChangeStop(Animator anim){
        yield return new WaitForSeconds(3f);

        anim.SetBool("isStopped", false);
    }

    IEnumerator WaitAndChangeFollowing(Animator anim){
        yield return new WaitForSeconds(3f);

        anim.SetBool("isFollowing", true);
    }
}