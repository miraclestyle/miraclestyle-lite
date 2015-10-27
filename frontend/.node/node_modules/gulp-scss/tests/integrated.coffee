expect = require("chai").expect
fs = require "fs"
q = require "q"
g = require "gulp"
gutil = require "gulp-util"
sourcemaps = require "gulp-sourcemaps"
removeMapFile = require("convert-source-map").removeMapFileComments
path = require "path"

describe "SCSS integration tests", ->
  scss = require "../src/scss"
  describe "Single File Case", ->
    right = {}
    before (done) ->
      targetPromises = [
        q.nfcall(
          fs.readFile,
          "./tests/data/single/source.css"
        ).then(
          (css) -> right.file = removeMapFile(css.toString "utf-8").trim()
        )
        q.nfcall(
          fs.readFile,
          "./tests/data/single/source.css.map"
        ).then(
          (map) ->
            right.sourcemap = JSON.parse(map)
            right.sourcemap.sources = right.sourcemap.sources.map(
              (file) -> path.relative(
                process.cwd(), path.resolve "./tests/data/single", file
              )
            )
        )
      ]
      q.all(targetPromises).done (-> done()), done
    after ->
      delete require.cache[require.resolve "../src/scss.coffee"]

    it "The file should be compiled properly", (done) ->
      compilationDefer = q.defer()
      g.src(
        "./tests/data/single/source.scss"
      ).pipe(
        sourcemaps.init()
      ).pipe(
        scss("bundleExec": true)
      ).pipe(
        sourcemaps.write("./", "includeContent": false)
      ).pipe(
        g.dest("./tests/results/single")
      ).once(
        "end",
        compilationDefer.resolve
      ).once("error", (e) ->
        compilationDefer.reject(e)
        throw e
      )

      compilationDefer.promise.then(
        -> q.all([
          q.nfcall fs.readFile, "./tests/results/single/source.css"
          q.nfcall fs.readFile, "./tests/results/single/source.css.map"
        ]).then(
          (data) ->
            expect(
              removeMapFile(data[0].toString "utf-8").trim()
            ).equal right.file
            expect(JSON.parse(data[1])).eql right.sourcemap
        )
      ).done (-> done()), done

  describe "Multiple Files Case", ->
    right = {}
    targetFiles = [
      "test1.css"
      "test2.css"
      "test3.css"
    ]
    before (done) ->
      promises = []
      targetFiles.forEach (file) ->
        promises.push q.nfcall(
          fs.readFile,
          path.join("./tests/data/multiple", file)
        ).then(
          (data) ->
            resultPath = path.join("./tests/results/multiple", file)
            if not right[resultPath]
              right[resultPath] = {}
            right[resultPath].content = removeMapFile(
              data.toString("utf-8")
            ).trim()
        )
        promises.push q.nfcall(
          fs.readFile,
          path.join("./tests/data/multiple", file + ".map")
        ).then(
          (data) ->
            resultPath = path.join("./tests/results/multiple", file)
            if not right[resultPath]
              right[resultPath] = {}
            right[resultPath].map = JSON.parse data.toString("utf-8")
            right[resultPath].map.sources = right[resultPath].map.sources.map(
              (file) -> path.relative(
                process.cwd()
                path.resolve "./tests/data/multiple", file
              )
            )
        )
      q.all(promises).done (-> done()), done

    it "The files should be compiled properly", (done) ->
      defer = q.defer()
      g.src((
        path.join(
          "./tests/data/multiple",
          gutil.replaceExtension(file, ".scss")
        ) for file in targetFiles
      )).pipe(
        sourcemaps.init()
      ).pipe(
        scss "bundleExec": true
      ).pipe(
        sourcemaps.write("./", "includeContent": false)
      ).pipe(
        g.dest("./tests/results/multiple")
      ).on("end", defer.resolve).once("error", defer.reject)

      defer.promise.then(
        ->
          files = targetFiles.map (file) ->
            path.join("./tests/results/multiple", file)

          promises = []
          files.forEach (file) ->
            promises.push q.nfcall(
              fs.readFile, file
            ).then(
              (data) ->
                expect(
                  removeMapFile(data.toString "utf-8").trim()
                ).equal(
                  right[file].content
                )
            )
            promises.push q.nfcall(
              fs.readFile, file + ".map"
            ).then((data) -> expect(JSON.parse data).eql right[file].map)
          q.all(promises).done (-> done()), done
      )
  describe "Glob test case", ->
    right = {}
    folders = ["test1", "test2", "test3"]
    before (done) ->
      promises = []
      folders.forEach (folder) ->
        result_path = path.join("tests/results/glob", folder, "source.css")
        promises.push(
          q.nfcall(
            fs.readFile,
            path.join("./tests/data/glob", folder, "source.css")
          ).then(
            (data) ->
              if not right[result_path]
                right[result_path] = {}
              right[result_path].content = removeMapFile(
                data.toString "utf-8"
              ).trim()
          )
          q.nfcall(
            fs.readFile,
            path.join("./tests/data/glob", folder, "source.css.map")
          ).then(
            (data) ->
              if not right[result_path]
                right[result_path] = {}
              right[result_path].map = JSON.parse data
              # BUG: gulp-sourcemaps can't generate correct file field
              delete right[result_path].map.file
              right[result_path].map.sources =
                right[result_path].map.sources.map (file) ->
                  path.relative(
                    process.cwd(),
                    path.resolve path.join("./tests/data/glob", folder),
                    file
                  )
          )
        )
      q.all(promises).done (-> done()), done

    it "The files should be compiled properly", (done) ->
      defer = q.defer()
      g.src(
        "./tests/data/glob/**/*.scss"
      ).pipe(
        sourcemaps.init()
      ).pipe(
        scss("bundleExec": true)
      ).pipe(
        sourcemaps.write(
          "./", "includeContent": false
        )
      ).pipe(
        g.dest("./tests/results/glob")
      ).once("end", defer.resolve).once("error", defer.reject)
      defer.promise.then(
        ->
          promises = []
          folders.forEach (folder) ->
            resultPath = path.join(
              "./tests/results/glob",
              folder,
              "source.css"
            )
            promises.push q.nfcall(
              fs.readFile,
              resultPath
            ).then(
              (data) ->
                expect(
                  removeMapFile(data.toString "utf-8").trim()
                ).equal right[resultPath].content
            )
            promises.push q.nfcall(
              fs.readFile,
              resultPath + ".map"
            ).then(
              (map) ->
                sourcemap = JSON.parse map
                # BUG: gulp-sourcemaps can't generate correct file field
                delete sourcemap.file
                expect(sourcemap).eql right[resultPath].map
            )
          q.all(promises)
      ).done (-> done()), done

  describe "Import test case", ->
    right = {}
    beforeEach (done) ->
      promises = [
        q.nfcall(
          fs.readFile,
          "./tests/data/imports/main.css"
        ).then(
          (data) -> right.content = removeMapFile(
            data.toString("utf-8")
          ).trim()
        )
        q.nfcall(
          fs.readFile,
          "./tests/data/imports/main.css.map"
        ).then(
          (data) ->
            right.map = JSON.parse data
            right.map.sources = right.map.sources.map (file) ->
              path.relative(
                process.cwd(),
                path.resolve "./tests/data/imports", file
              )
        )
      ]
      q.all(promises).done (-> done()), done

    it "The code should be compiled properly", (done) ->
      defer = q.defer()
      g.src(
        "./tests/data/imports/main.scss"
      ).pipe(
        sourcemaps.init()
      ).pipe(
        scss "bundleExec": true
      ).pipe(
        sourcemaps.write("./", ("includeContent": false))
      ).pipe(
        g.dest("./tests/results/imports")
      ).once("end", defer.resolve).once("error", defer.reject)

      defer.promise.then(
        ->
          promises = []
          promises.push q.nfcall(
            fs.readFile,
            "./tests/results/imports/main.css"
          ).then(
            (data) -> expect(
              removeMapFile(data.toString "utf-8").trim()
            ).equal right.content
          )
          promises.push q.nfcall(
            fs.readFile,
            "./tests/results/imports/main.css.map"
          ).then((data) -> expect(JSON.parse data).eql right.map)
          q.all promises
      ).done (-> done()), done
