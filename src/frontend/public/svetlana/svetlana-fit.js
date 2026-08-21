/* Keep the authored Svetlana model framed as a full-body avatar. */
(async function(){
  'use strict';
  let THREE=null;
  try{THREE=await import('./vendor/three/0.179.1/three.module.js');}catch(_){return;}
  let tries=0;
  const timer=setInterval(function(){
    const avatar=window.SvetlanaAvatar;
    if(!avatar?.camera || !avatar?.model) { if(++tries>120) clearInterval(timer); return; }
    clearInterval(timer);
    try{
      const box=new THREE.Box3().setFromObject(avatar.model);
      const size=box.getSize(new THREE.Vector3());
      const center=box.getCenter(new THREE.Vector3());
      const height=Math.max(size.y,0.1);
      const fov=(avatar.camera.fov*Math.PI)/180;
      const distance=Math.max(1.8,(height*0.58)/Math.tan(fov/2));
      avatar.camera.position.set(center.x,center.y+height*0.02,center.z+distance);
      avatar.camera.near=Math.max(0.01,distance/100);
      avatar.camera.far=Math.max(20,distance*20);
      avatar.camera.lookAt(center.x,center.y+height*0.03,center.z);
      avatar.camera.updateProjectionMatrix();
      avatar.fullBodyFrame={height,center:{x:center.x,y:center.y,z:center.z},distance};
    }catch(_){ }
  },100);
})();
