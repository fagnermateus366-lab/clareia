'use client';
import dynamic from 'next/dynamic';
const Gallery=dynamic(()=>import('../components/Gallery'),{ssr:false,loading:()=> <main className="loading-screen">Preparando a biblioteca 3D…</main>});
export default function Page(){return <Gallery/>;}
