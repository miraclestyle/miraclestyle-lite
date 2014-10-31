var beautify = require('js-beautify').js_beautify,
    fs = require('fs'),
    path = require('path'),
    string = require('string');

var config = {
    "indent_size": 2,
    "indent_char": " ",
    "indent_level": 0,
    "indent_with_tabs": false,
    "preserve_newlines": true,
    "max_preserve_newlines": 10,
    "jslint_happy": true,
    "space_after_anon_function": false,
    "brace_style": "collapse",
    "keep_array_indentation": false,
    "keep_function_indentation": false,
    "space_before_conditional": true,
    "break_chained_methods": false,
    "eval_code": false,
    "unescape_strings": false,
    "wrap_line_length": 79
};

var walk = function(dir, done) {
  var results = [];

  fs.readdir(dir, function(err, list) {
    if (err) return done(err);
    var pending = list.length;
    if (!pending) return done(null, results);
    var i = list.indexOf('libraries');
    if (i !== -1)
    {
      list.splice(i, 1);
      --pending;
    }
    
    list.forEach(function(file) {
      file = dir + '/' + file;
      s = string(file);
      fs.stat(file, function(err, stat) {
        if (stat && stat.isDirectory()) {
          walk(file, function(err, res) {
              results = results.concat(res);
              if (!--pending) done(null, results);
            });
          
        } else {
          
          results.push(file);
          
          if (!--pending) done(null, results);
        }
      });
    });
  });
};

var filePath = path.join(__dirname, '../../static/angular');

walk(filePath, function (err, files) {
  var results = [];
  files.forEach(function (file) {
    if (string(file).endsWith('.js'))
    {
      results.push(file);
    }
  });
  
  results.forEach(function (file) {
    var pending = results.length;
    fs.readFile(file, 'utf8', function (err, data) {
        if (err) {
            throw err;
        }
        console.log('----------', file, '----------');
        console.log(beautify(data, config));
    });
  });
  
});

/*glob(filePath + '/*.js', function (err, rootfiles) {
  console.log(filePath, '/components/*.js');
  glob(filePath + '/components/*.js', function (err, files) {
    console.log(rootfiles, files);
  });
});*/
