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
            var cmd = '';
            if (e.changed.indexOf('.js') !== -1) {
                cmd = 'javascript';
            }
            console.log('Building');

            console.log('End building');
        }, 200);
    });
});

// The default task (called when you run `gulp` from cli)
gulp.task('default', ['css', 'seo-css', 'javascript', 'templates']);
