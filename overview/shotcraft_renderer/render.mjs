// Local-only rendering. Props are data; the AI cannot supply JS/HTML or URLs.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {bundle} from '@remotion/bundler';
import {ensureBrowser,selectComposition,renderMedia,makeCancelSignal} from '@remotion/renderer';

const root=path.dirname(fileURLToPath(import.meta.url));
async function installedWindowsChrome(){
  if(process.platform!=='win32')return null;
  for(const base of [process.env.ProgramFiles,process.env['ProgramFiles(x86)'],process.env.LOCALAPPDATA]){
    if(!base)continue;
    const exe=path.join(base,'Google','Chrome','Application','chrome.exe');
    try{await fs.access(exe);return exe;}catch{}
  }
  return null;
}
const [propsFile,outputFile,bundleDir,pauseFile]=process.argv.slice(2);
if(propsFile==='--browser'){
  let previous=-1;
  const info=await ensureBrowser({onBrowserDownload:()=>({onProgress:({percent})=>{const current=Math.floor(percent*10)*10;if(current!==previous){previous=current;process.stdout.write(`Browser ${current}%\n`)}}})});
  console.log(JSON.stringify(info));
}else{
  const props=JSON.parse(await fs.readFile(propsFile,'utf8'));
  if(!props.moments?.length||!Number.isInteger(props.durationInFrames))throw new Error('Invalid animation manifest');
  let cached=false;try{await fs.access(path.join(bundleDir,'index.html'));cached=true}catch{}
  const serveUrl=cached?bundleDir:await bundle({entryPoint:path.join(root,'src/index.tsx'),outDir:bundleDir,enableCaching:true});
  const {cancel,cancelSignal}=makeCancelSignal();
  const timer=setInterval(async()=>{if(pauseFile){try{await fs.access(pauseFile);cancel()}catch{}}},300);
  try{
    const renderPass=async(browserOptions)=>{
      const composition=await selectComposition({serveUrl,id:'ClareiaShotcraft',inputProps:props,...browserOptions});
      let previous=-1;
      await renderMedia({serveUrl,composition,inputProps:props,codec:'h264',outputLocation:outputFile,
        concurrency:1,crf:16,x264Preset:'ultrafast',imageFormat:'jpeg',jpegQuality:94,...browserOptions,
        cancelSignal,overwrite:true,muted:true,logLevel:'error',
        onProgress:({progress})=>{const current=Math.floor(progress*10)*10;if(current!==previous){previous=current;process.stdout.write(`Progress ${current}%\n`)}}});
    };
    try {
      await renderPass({});
    } catch(error) {
      const webglFailure=/Error creating WebGL context|WebGL context could not be created/i.test(String(error));
      if(!webglFailure||!props.moments.some(moment=>moment.receita?.startsWith('volume_')))throw error;
      console.log('WebGL indisponivel no navegador isolado; repetindo a cena com Chrome completo em modo sem janela.');
      const browserExecutable=await installedWindowsChrome();
      await renderPass({chromeMode:'chrome-for-testing',...(browserExecutable?{browserExecutable}:{})});
    }
    console.log('Complete');
  }finally{clearInterval(timer)}
}
