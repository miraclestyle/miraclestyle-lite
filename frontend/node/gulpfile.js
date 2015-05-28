var gulp = require('gulp');
var scss = require('gulp-scss');
var autoprefixer = require('gulp-autoprefixer');
var minifyCss = require('gulp-minify-css');
var angularInjector = require('gulp-angular-injector');
var uglify = require('gulp-uglify');

gulp.task('css', function () {
    return gulp.src('raw/style.css')
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
        .pipe(gulp.dest('../client/dist'));
});

// The default task (called when you run `gulp` from cli)
gulp.task('default', ['css', 'javascript', 'templates']);
