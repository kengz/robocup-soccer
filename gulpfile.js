// dependencies
var gulp = require('gulp');
var q = require('q');
var cp = require('child_process');

// file paths

// Design for isochrone
// node stores neigh n weight (distance)
// pick a set of gas stations, diff other set of non-gas
// for each non-gas z, the time is min({z,{gas}})

/////////////////////
// Normal plotting //
/////////////////////

// gulp top level tasks
gulp.task('default', ['start']);
gulp.task('start', ['run', 'rerun']);


gulp.task('rerun', ['run'], function(){
    gulp.watch('./**/*.java', ['run']);
    gulp.watch('./data/*.txt', ['run']);
    // gulp.watch('./data/*.csv', ['parse', 'run']);
})

// Reloading browserSync
gulp.task('run', exec.bind(null, 'make'));

// gulp.task('parse', exec.bind(null, 'node data/parser.js'));

// Deploying bot
// terminal exec task with promise: use as exec.bind(<command>)
function exec(arg) {
    var defer = q.defer();
    cp.exec(arg, function(err, stdout, stderr) {
        if (err) throw err
        console.log(stdout);
        defer.resolve(err)
    })
    return defer.promise;
}
