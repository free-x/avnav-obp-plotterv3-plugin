/*
OBP plotter V3 simple brightness widget
*/

let widgetServer={
    name:"obpPlotter",
    /**
     * if our plugin would like to use event handlers (like button click)
     * we need to register handler functions
     * this can be done at any time - but for performance reasons this should be done
     * inside an init function
     * @param context - the context - this is an object being the "this" for all other function calls
     *                  there is an empty eventHandler object in this context.
     *                  we need to register a function for every event handler we would like to use
     *                  later in renderHtml
     */
    initFunction:(context)=>{
        /**
         * each event handler we register will get the event as parameter
         * when being called, this is pointing to the context (not the event target - this can be obtained by ev.target)
         * in this example we issue a request to the python side of the plugin using the
         * global variable AVNAV_BASE_URL+"/api" and appending a further url
         * We expect the response to be json
         * @param ev
         */
        const fetchCurrent=()=>{
            return fetch(AVNAV_BASE_URL+"/api/query?_="+(new Date()).getTime())
            .then((data)=>data.json())
            .then((json)=>{
                if (json.status !== "OK"){
                    context.duty="???"
                    context.error=json.status||"Error"
                    context.brightness="Error";
                }
                else{
                    context.duty=json.duty+"";
                    context.error=json.error;
                    context.brightness=(json.brightnessError !== null)?"Error":json.brightness
                }
                context.triggerRedraw();
            })
        }
        const plusMinus=(plus)=>{
            let url=AVNAV_BASE_URL+"/api/"+(plus?"plus":"minus")+"?_="+(new Date()).getTime();
            fetch(url)
            .then((data)=>data.json())
            .then((json)=>{
                if (json.status !== 'OK'){
                    throw new Error(json.status+"");
                }
                return fetchCurrent();
            })
            .catch((err)=>avnav.api.showToast("ERROR: "+err));

        }
        context.eventHandler.minusClick=(ev)=>{
            plusMinus(false);
        }
        context.eventHandler.plusClick=(ev)=>{
            plusMinus(true);
        }
        fetchCurrent();
        context.timer=window.setInterval(fetchCurrent,1000);
        
    },
    /**
     * a function that will render the HTML content of the widget
     * normally it should return a div with the class widgetData
     * but basically you are free
     * If you return null, the widget will not be visible any more.
     * @param props
     * @returns {string}
     */
    renderHtml:function(props){
        /**
         * in our html below we assign an event handler to the button
         * just be careful: this is not a strict W3C conforming HTML syntax:
         * the event handler is not directly js code but only the name(!) of the registered event handler.
         * it must be one of the names we have registered at the context.eventHandler in our init function
         * Unknown handlers or pure java script code will be silently ignored!
         */
        var buttonClass="plusminus";
        //as we are not sure if the browser supports template strings we use the AvNav helper for that...
        var replacements={
            duty:this.error?"Error":this.duty,
            disabled: '',
            errorClass: this.error?"error":"",
            brightness: this.brightness
        };
        var template='<div class="widgetData">' +
            '<div class="row">'+
            '<button class="plusminus" ${disabled}  onclick="minusClick">-</button>' +
            '<button class="plusminus" ${disabled}  onclick="plusClick">+</button>' +
            '</div>'+
            '<div class="server ${errorClass}">${duty}</div>'
        if (props.showLuminance){
            template+='<div class="luminance"><span class="label">Lum</span>${brightness}</div>';
        }    
        template+='</div>';        
        return avnav.api.templateReplace(template,replacements);
    },
    caption: "Brightness",
    unit: "",
    finalizeFunction:(context)=>{
        window.clearInterval(context.timer);
    }
};

avnav.api.registerWidget(widgetServer,{
    showLuminance: {type:'BOOLEAN',default:false},
    formatter: false,
    formatterParameters:false,
    unit: false
});
avnav.api.log("obp plotter plugin widgets registered");
