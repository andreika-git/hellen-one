/* 
  ############################################################################################
  # Hellen-One: A 3D-component VRML rendering server script.
  # (c) andreika <prometheus.pcb@gmail.com>
  ############################################################################################
  
  Node.js is required to run this script: https://nodejs.org/en/download/
  Also please install Puppeteer and PNGJS Node modules before running:
     > npm install --prefix ./bin/render_vrml puppeteer
     > npm install --prefix ./bin/render_vrml pngjs
*/

try {
	const puppeteer = require("puppeteer");
	var PNG = require("pngjs").PNG;
	// built-in modules
	var fs = require("fs");
	const zlib = require("zlib"); 

	var args = process.argv.slice(2);
	if (args.length < 3) {
		console.log("* Error! Please specify correct arguments to run this script!");
		process.exit(1)
	}
	// arguments
	var vrmlFile = args[0];
	var compImgFile = args[1];
	var dpi = parseFloat(args[2]);
	
	console.log("* Starting Puppeteer (" + vrmlFile + " dpi=" + dpi + "...");

	(async () => {
		const browser = await puppeteer.launch();
  		const page = await browser.newPage();
  		
	  	var contentHtml = fs.readFileSync("bin/render_vrml/render_vrml.html", "utf8");
	  	
	  	console.log("* Reading the input file...");
  		var vrmlData = fs.readFileSync(vrmlFile);
  		if (vrmlFile.endsWith('.gz')) {
			vrmlData = zlib.gunzipSync(vrmlData);
		}
	  	var vrmlDataBase64 = vrmlData.toString("base64");
	  	
	  	// injecting the data to the client script
	  	contentHtml = contentHtml.replace("___SCREEN_DPI___", dpi);
  		contentHtml = contentHtml.replace("___VRML_DATA___", "data:application/gzip;base64," + vrmlDataBase64);

		page.on("console", message => {
				message.args().forEach(async (arg) => {
					const val = await arg.jsonValue()
					if (JSON.stringify(val) !== JSON.stringify({})) 
						console.log(`* Script: ` + val)
					else {
						const { type, subtype, description } = arg._remoteObject;
						console.log(`* Script: ${type} ${subtype}:\n ${description}`)
					}
				})
			})
    		.on("pageerror", ({ message }) => console.log(`* LOG_ERROR: ` + message))
    		.on("response", response => console.log(`* Loading: ` + `${response.status()} ${response.url()}`))
	    	.on("requestfailed", request => console.log(`* Loading Failed: ` + `${request.failure().errorText} ${request.url()}`));

		console.log("* Executing the script...");
		await page.setContent(contentHtml);
		console.log("* Waiting for completion...");
		const watchDog = page.waitForFunction("document.done");
		await watchDog;

		var screenWidth = await page.evaluate(() => document.compImgWidth);
		var screenHeight = await page.evaluate(() => document.compImgHeight);
	  	console.log("* Saving the screenshot (" + screenWidth + "x" + screenHeight + ")");
  		await page.setViewport({width: screenWidth, height: screenHeight, deviceScaleFactor: 1, });
	  	await page.screenshot({path: compImgFile, omitBackground: true});
	  	await browser.close();
	  	console.log("* Done! Exiting...");
	})();

} catch(e) {
    if (e.message.indexOf("Cannot find module") !== -1) {
    	console.error("Error! `Puppeteer` or `pngjs` library is not installed? Try running `npm install --prefix ./bin/render_vrml`.");
    }
    console.log(e);
    process.exit(e.code);
}
