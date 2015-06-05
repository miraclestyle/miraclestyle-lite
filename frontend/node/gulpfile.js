var gulp = require('gulp');
var scss = require('gulp-scss');
var autoprefixer = require('gulp-autoprefixer');
var minifyCss = require('gulp-minify-css');
var angularInjector = require('gulp-angular-injector');
var uglify = require('gulp-uglify');
var exec = require('child_process').exec;

gulp.task('css', function () {
    return gulp.src('raw/style.css')
        .pipe(scss())
        .pipe(autoprefixer())
        .pipe(minifyCss())
        .pipe(gulp.dest('../client/dist'));
});

gulp.task('seo-css', function () {
    return gulp.src('raw/seo.css')
        .pipe(scss())
        .pipe(autoprefixer())
        .pipe(minifyCss())
        .pipe(gulp.dest('../client/dist'));
});

gulp.task('javascript', function () {
    return gulp.src('raw/app.js')
        .pipe(angularInjector())
        .pipe(uglify())
        .pipe(gulp.dest('../client/dist'));
});

gulp.task('templates', function () {
    return gulp.src('raw/templates.js')
        .pipe(angularInjector())
        .pipe(uglify())
        .pipe(gulp.dest('../client/dist'));
});

var timer = null;

gulp.task('watch', function () {
    gulp.watch('../client/src/**').on('change', function (e) {
        if (timer) {
            clearTimeout(timer);
        }
        timer = setTimeout(function () {
            var arg = '',
                command,
                build;
            if (e.path.indexOf('.js') !== -1) {
                arg = 'javascript';
            }
            if (e.path.indexOf('.css') !== -1) {
                arg = 'css';
            }

            if (e.path.indexOf('.css') !== -1 && e.path.indexOf('seo/') !== -1) {
                arg = 'seo-css';
            }
            if (e.path.indexOf('.html') !== -1) {
                arg = 'templates';
            }
            command = 'python ../settings.py ' + arg;
            build = 'Completed ' + command;
            console.log('Running ' + command);
            console.time(build);
            exec(command, function (error, stdout, stderr) {
                if (error !== null) {
                    console.error('Failed build: ' + error);
                } else {
                    console.log('Succesfull build');
                }
                console.timeEnd(build);
            });
        }, 2000);
    });
});

// The default task (called when you run `gulp` from cli)
gulp.task('default', ['css', 'seo-css', 'javascript', 'templates']);