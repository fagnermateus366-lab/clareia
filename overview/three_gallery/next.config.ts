import type {NextConfig} from 'next';
import path from 'node:path';
const config:NextConfig={output:'export',basePath:'/3d',trailingSlash:true,images:{unoptimized:true},
  webpack(config){
    config.resolve.alias['@three-library']=path.resolve(__dirname,'../shotcraft_renderer/src/components/3d-library');
    for(const name of ['three','@react-three/fiber','@react-three/drei'])
      config.resolve.alias[name]=path.resolve(__dirname,'node_modules',name);
    return config;
  }};
export default config;
