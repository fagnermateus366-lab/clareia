import './globals.css';
import type {Metadata} from 'next';
export const metadata:Metadata={title:'Clareia · Biblioteca 3D',description:'Modelos volumétricos locais, iluminação e animação em tempo real.'};
export default function Layout({children}:{children:React.ReactNode}){return <html lang="pt-BR"><body>{children}</body></html>;}
