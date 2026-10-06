import {ReactNode, useState} from 'react';
import {Leaf, ArrowUpRight, FileText, LayoutGrid, Settings2, X} from 'lucide-react';
import {MotionConfig, motion} from 'motion/react';

export async function api<T=any>(url:string, options?:RequestInit):Promise<T>{
  let response:Response;
  try{response=await fetch(url,options);}catch{throw Error('Сервер недоступен. Запустите локальную демоверсию по README.');}
  let body:any;try{body=await response.json();}catch{throw Error('Это предпросмотр интерфейса. Для обработки нужен локальный сервер - инструкция в GitHub.');}
  if(!response.ok)throw Error(typeof body.detail==='string'?body.detail:'Не удалось выполнить запрос. Проверьте введённые данные.');
  return body;
}
export const post=(url:string,value:unknown)=>api(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(value)});
export const money=(n:number)=>new Intl.NumberFormat('ru-RU').format(n)+' ₽';
export const time=(n:number)=>`${Math.floor(n/60).toString().padStart(2,'0')}:${Math.floor(n%60).toString().padStart(2,'0')}`;
export function ErrorBox({error}:{error:string}){return error?<div className="error" role="alert">{error}</div>:null;}
export function Shell({title,slug,nav,tab,onTab,children}:{title:string;slug:string;nav:string[];tab:number;onTab:(n:number)=>void;children:ReactNode}){
 return <MotionConfig reducedMotion="user"><header className="topbar"><a className="brand" href="../"><span className="brand-icon"><Leaf size={19}/></span>{title}</a><div className="toplinks"><span className="tag optional">Портфолио / демо</span><a href={`https://github.com/famelikolbut5/${slug}`} target="_blank" rel="noreferrer">Исходный код </a></div></header><div className="app-layout"><aside className="sidebar">{nav.map((name,n)=>{const Icon=[LayoutGrid,FileText,Settings2][n%3];return <button key={name} className={'nav-button '+(tab===n?'active':'')} onClick={()=>onTab(n)}><Icon size={17}/>{name}</button>})}<div className="side-note">Независимый проект.<br/>Синтетические данные.<br/>Python + TypeScript.</div></aside><motion.main className="workspace" initial={{opacity:0}} animate={{opacity:1}} transition={{duration:.25}}>{children}</motion.main></div></MotionConfig>;
}
export function About({title,children}:{title:string;children:ReactNode}){return <><div className="heading"><h1>Как устроен {title}</h1></div><section className="panel"><div className="panel-body stack">{children}</div></section></>;}
