import {useState,useEffect} from 'react';
export function usePeaks(url:string){
 const [peaks,setPeaks]=useState<number[]>(Array(90).fill(.03));
 useEffect(()=>{let stopped=false;const controller=new AbortController();let context:AudioContext|undefined;(async()=>{try{const response=await fetch(url,{signal:controller.signal});if(!response.ok)return;const bytes=await response.arrayBuffer();context=new AudioContext();const buffer=await context.decodeAudioData(bytes);const channel=buffer.getChannelData(0);const block=Math.max(1,Math.floor(channel.length/90));const raw=Array.from({length:90},(_,i)=>{let peak=0;for(let n=i*block;n<Math.min((i+1)*block,channel.length);n+=4)peak=Math.max(peak,Math.abs(channel[n]));return peak});const maximum=Math.max(...raw,.01);if(!stopped)setPeaks(raw.map(n=>n/maximum))}catch{}finally{context?.close().catch(()=>{})}})();return()=>{stopped=true;controller.abort()}},[url]);return peaks;
}
