(function(){
    const API="api/"
    let toast;
    let toastTimer;
    const showToast=(txt,time)=>{
        if (toastTimer !== undefined){
            window.clearTimeout(toastTimer);
        }
        toastTimer=window.setInterval(()=>{
            toast.classList.add('hidden');
        }, time || 5000);
        toast.textContent=txt;
        toast.classList.remove('hidden');
    }
    const sendApiRequest= async (code)=>{
        let json;
        try{
        let rt=await fetch(API+code);
        if (rt.status !== 200){
            throw new Error("invalid response: "+rt.status);
        }
        json=await rt.json();
        if (json.status !== 'OK'){
            throw new Error("error: "+json.status);
        }
        }catch (error){
            showToast("error: "+error);
            return;
        }
        return json;
    }
    const apiFunctions={
        volumeMinus:'volumeMinus',
        volumePlus:'volumePlus',
        dimmMinus:'minus',
        dimmPlus:'plus',
        save: 'saveCurrent',
        defaultBrightness: 'defaultStep'
    }
    let currentBrightness;
    let currentVolume;
    let currentLuminance;
    let adaptive;
    const updateValues = async () => {
        let data = await sendApiRequest("query");
        if (data) {
            if (data.duty !== undefined) {
                currentBrightness.textContent = data.duty.toFixed(2);
            }
            if (data.volume !== undefined){
                currentVolume.textContent = data.volume;
            }
            if (data.brightnessError !== null){
                currentLuminance.textContent ="ERROR: "+data.brightnessError;
            }
            else{
                currentLuminance.textContent = data.brightness;
            }
            adaptive.checked=data.auto;
        }
    }
    window.addEventListener('load',()=>{
        currentBrightness=document.getElementById('currentBrightness');
        currentVolume=document.getElementById('currentVolume');
        currentLuminance=document.getElementById('currentLuminance');
        toast=document.getElementById('toast');
        toast.addEventListener('click',()=>toast.classList.add('hidden'));
        window.setInterval(async ()=>{
            updateValues();
        },1000);
        for (let k in apiFunctions){
            let el=document.getElementById(k);
            if (el){
                let command=apiFunctions[k];
                el.addEventListener('click',async ()=>{
                    let rt=await sendApiRequest(command);
                    await updateValues();
                    if (k === 'save' ){
                        alert("Saved: "+rt.saved)
                    }
                })
            }
        }
        adaptive=document.getElementById('autoOn');
        if (adaptive){
            adaptive.addEventListener('change',async ()=>{
                if (adaptive.checked){
                    await sendApiRequest('autoOn');    
                }
                else{
                    await sendApiRequest('autoOff');
                }
                await updateValues();
            })
        }
    })
})();