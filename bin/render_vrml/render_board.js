/* 
  ############################################################################################
  # Hellen-One: A board rendering server script.
  # (c) andreika <prometheus.pcb@gmail.com>
  ############################################################################################
  
  Node.js is required to run this script: https://nodejs.org/en/download/
  Also please install PNGJS Node modules before running:
     > npm install --prefix ./bin/render_vrml pngjs
*/

function getPixel(img, x, y) {
    if (x < 0 || y < 0 || x >= img.width || y >= img.height)
    	return [0, 0, 0, 0];
	var idx = (img.width * y + x) << 2;
	return [ img.data[idx], img.data[idx + 1], img.data[idx + 2], img.data[idx + 3] ];
}

function createBoardImg(pcbImg, outlineImg, compImg, compImgOffset) {
	var boardImg = new PNG({ 
		width: Math.max(pcbImg.width, outlineImg.width, compImg.width), 
		height: Math.max(pcbImg.height, outlineImg.height, compImg.height) });
	var pcbOffY = (pcbImg.height < outlineImg.height) ? -(outlineImg.height - pcbImg.height) : 0;
	// Blit the pcbImg using the outlineImg mask and add compImg.
	// We cannot use PNG.bitblt() for that
	for (var y = 0; y < boardImg.height; y++) {
    	for (var x = 0; x < boardImg.width; x++) {
        	var bPixel = getPixel(pcbImg, x, y + pcbOffY);
            var cPixel = getPixel(compImg, x + compImgOffset[0], y + compImgOffset[1]);
        	var a = parseFloat(cPixel[3]) / 255.0;
        	var na = 1.0 - a;
        	var idx = (boardImg.width * y + x) << 2;
        	boardImg.data[idx + 0] = na * bPixel[0] + a * cPixel[0];
        	boardImg.data[idx + 1] = na * bPixel[1] + a * cPixel[1];
        	boardImg.data[idx + 2] = na * bPixel[2] + a * cPixel[2];
        	boardImg.data[idx + 3] = na * getPixel(outlineImg, x, y)[0] + a * 255;
		}
	}
	return boardImg;
}

try {
	var PNG = require("pngjs").PNG;
	// built-in modules
	var fs = require("fs");

	var args = process.argv.slice(2);
	if (args.length < 4) {
		console.log("* Error! Please specify correct arguments to run this script!");
		process.exit(1)
	}
	// arguments
	var pcbImgFile = args[0];
	var outlineImgFile = args[1];
	var compImgFile = args[2];
	var boardImgFile = args[3];
	var compImgOffset = args[4].split(",").map((x) => parseInt(x));
	
	console.log("* Reading the pcb image...");
	var pcbImg = PNG.sync.read(fs.readFileSync(pcbImgFile));
  	console.log("* Reading the components image with offset (" + compImgOffset[0] + "," + compImgOffset[1] + ")...");
	var compImg = PNG.sync.read(fs.readFileSync(compImgFile));
  	console.log("* Reading the outline image...");
	var outlineImg = PNG.sync.read(fs.readFileSync(outlineImgFile));

	console.log("* Creating the final board image...");
	var boardImg = createBoardImg(pcbImg, outlineImg, compImg, compImgOffset);
  	console.log("* Saving the board image...");
	fs.writeFileSync(boardImgFile, PNG.sync.write(boardImg, { colorType: 6 }));

  	console.log("* Done! Exiting...");

} catch(e) {
    if (e.message.indexOf("Cannot find module") !== -1) {
    	console.error("Error! `pngjs` library is not installed? Try running `npm install --prefix ./bin/render_vrml`.");
    }
    console.log(e);
    process.exit(e.code);
}
