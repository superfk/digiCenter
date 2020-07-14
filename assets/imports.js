let fs = require('fs');
const path = require('path');
// const electron = require('electron');
// const app = electron.app;
// const appRootPath = app.getAppPath();

// const links = document.querySelectorAll('link[rel="import"]')

const links = ['sections/config.html','sections/seqEditor.html','sections/run.html', 'sections/report.html']

// Import and add each page to the DOM
Array.prototype.forEach.call(links, (link) => {
  
  const fullPath = path.join(path.dirname(__dirname), link)

  // let template = link.import.querySelector('.task-template')
  fs.readFile(fullPath, (err, html) => {
    if (err){
      console.error(err)
    }else {
      parser = new DOMParser();
      doc = parser.parseFromString(html, "text/html")
      let template = doc.querySelector('.task-template')
      let clone = document.importNode(template.content, true)
      document.querySelector('.content').appendChild(clone)
    }
  })
})
