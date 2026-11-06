/** Wrap at word boundaries; fitting still measures the complete geometry. */
export function wrapWords(text:string,maxChars:number){
 const lines:string[]=[];let line='';
 for(const word of text.split(/\s+/).filter(Boolean)){
  if(line&&line.length+word.length+1>maxChars){lines.push(line);line=word;}else line+=(line?' ':'')+word;
 }
 if(line)lines.push(line);return lines.join('\n');
}
