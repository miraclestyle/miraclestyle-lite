// Version (see package.json)
// AngularJS simple file upload directive
// this directive uses an iframe as a target
// to enable the uploading of files without
// losing focus in the ng-app.
//
// <div ng-app="app">
//   <div ng-controller="mainCtrl">
//    <form ng-attr-action="/uploads"
//      ng-upload="completed(content)">
//      ng-upload-loading="loading()"
//      <input type="file" name="avatar"></input>
//      <input type="submit" value="Upload"
//         ng-disabled="$isUploading"></input>
//    </form>
//  </div>
// </div>
//
//  angular.module('app', ['ngUpload'])
//    .controller('mainCtrl', function($scope) {
//      $scope.loading = function() {
//        console.log('loading...');
//      }
//      $scope.completed = function(content) {
//        console.log(content);
//      };
//  });
//
angular.module('app')
    .directive('uploadSubmit', ["$parse", function ($parse) {
        // Utility function to get the closest parent element with a given tag
        function getParentNodeByTagName(element, tagName) {
            element = angular.element(element);
            var parent = element.parent();
            tagName = tagName.toLowerCase();

            if (parent && parent[0].tagName.toLowerCase() === tagName) {
                return parent;
            } else {
                return !parent ? null : getParentNodeByTagName(parent, tagName);
            }
        }
        return {
            restrict: 'AC',
            link: function (scope, element, attrs) {
                element.bind('click', function ($event) {
                    // prevent default behavior of click
                    if ($event) {
                        $event.preventDefault();
                        $event.stopPropagation();
                    }

                    if (element.attr('disabled')) {
                        return;
                    }
                    var form = getParentNodeByTagName(element, 'form');
                    form.triggerHandler('submit');
                    form[0].submit();
                });
            }
        };
    }])
    .directive('ngUpload', ["$log", "$parse", "$document", "$rootScope", "errorHandling", "modelsUtil",
        function ($log, $parse, $document, $rootScope, errorHandling, modelsUtil) {
            var iframeID = 1;
            // Utility function to get meta tag with a given name attribute
            function getMetaTagWithName(name) {
                var head = $document.find('head');
                var match;

                angular.forEach(head.find('meta'), function (element) {
                    if (element.getAttribute('name') === name) {
                        match = element;
                    }
                });

                return angular.element(match);
            }

            return {
                require: 'form',
                restrict: 'AC',
                link: function (scope, element, attrs, ctrl) {
                    // Give each directive instance a new id
                    iframeID++;

                    var formController = ctrl;

                    function setLoadingState(state) {
                        scope.$isUploading = state;
                    }

                    var options = {};
                    // Options (just 1 for now)
                    // Each option should be prefixed with 'upload-options-' or 'uploadOptions'
                    // {
                    //    // add the Rails CSRF hidden input to form
                    //    enableRailsCsrf: bool
                    // }
                    var fn = attrs.ngUpload ? $parse(attrs.ngUpload) : angular.noop;
                    var errorFn = attrs.ngUploadError ? $parse(attrs.ngUploadError) : angular.noop;
                    var loading = attrs.ngUploadLoading ? $parse(attrs.ngUploadLoading) : null;
                    var opts = scope.$eval(attrs.ngUploadOptions) || {};
                    var normalize = (angular.isDefined(opts.normalize) ? opts.normalize : true);

                    if (attrs.hasOwnProperty("uploadOptionsConvertHidden")) {
                        // Allow blank or true
                        options.convertHidden = attrs.uploadOptionsConvertHidden != "false";
                    }

                    if (attrs.hasOwnProperty("uploadOptionsEnableRailsCsrf")) {
                        // allow for blank or true
                        options.enableRailsCsrf = attrs.uploadOptionsEnableRailsCsrf != "false";
                    }

                    if (attrs.hasOwnProperty("uploadOptionsBeforeSubmit")) {
                        options.beforeSubmit = $parse(attrs.uploadOptionsBeforeSubmit);
                    }

                    element.attr({
                        'target': 'upload-iframe-' + iframeID,
                        'method': 'post',
                        'enctype': 'multipart/form-data',
                        'encoding': 'multipart/form-data'
                    });

                    var config = {
                        url: element.attr('action')
                    };

                    var iframe = angular.element(
                        '<iframe name="upload-iframe-' + iframeID + '" ' +
                        'border="0" width="0" height="0" ' +
                        'style="width:0px;height:0px;border:none;display:none">'
                    );

                    // If enabled, add csrf hidden input to form
                    if (options.enableRailsCsrf) {
                        var input = angular.element("<input />");
                        input.attr("class", "upload-csrf-token");
                        input.attr("type", "hidden");
                        input.attr("name", getMetaTagWithName('csrf-param').attr('content'));
                        input.val(getMetaTagWithName('csrf-token').attr('content'));

                        element.append(input);
                    }
                    element.after(iframe);

                    setLoadingState(false);
                    // Start upload
                    element.bind('submit', function uploadStart() {
                        // if form is invalid don't submit (e.g. keypress 13)
                        if (formController && formController.$invalid) return false;
                        // perform check before submit file
                        if (options.beforeSubmit && options.beforeSubmit(scope, {}) == false) return false;

                        // bind load after submit to prevent initial load triggering uploadEnd
                        iframe.bind('load', uploadEnd);

                        // If convertHidden option is enabled, set the value of hidden fields to the eval of the ng-model
                        if (options.convertHidden) {
                            angular.forEach(element.find('input'), function (el) {
                                var _el = angular.element(el);
                                if (_el.attr('ng-model') &&
                                    _el.attr('type') &&
                                    _el.attr('type') == 'hidden') {
                                    _el.attr('value', scope.$eval(_el.attr('ng-model')));
                                }
                            });
                        }

                        if (!scope.$$phase) {
                            scope.$apply(function () {
                                if (loading) loading(scope);
                                setLoadingState(true);
                            });
                        } else {
                            if (loading) loading(scope);
                            setLoadingState(true);
                        }

                        scope.$broadcast('ngUploadSubmit');
                        $rootScope.$broadcast('disableUI', true);

                    });

                    // Finish upload
                    function uploadEnd() {
                        // unbind load after uploadEnd to prevent another load triggering uploadEnd
                        iframe.unbind('load');
                        if (!scope.$$phase) {
                            scope.$apply(function () {
                                setLoadingState(false);
                            });
                        } else {
                            setLoadingState(false);
                        }
                        // Get iframe body contents
                        var bodyContent = (iframe[0].contentDocument ||
                            iframe[0].contentWindow.document).body;
                        var content;
                        try {
                            content = angular.fromJson(bodyContent.innerText || bodyContent.textContent);
                        } catch (e) {
                            // Fall back to html if json parse failed
                            content = bodyContent.innerHTML;
                            $log.warn('Response is not valid JSON');
                        }

                        var response = {
                                content: {
                                    data: content
                                }
                            },
                            noErrors = (content && angular.isObject(content) && !content.errors);
                        // if outside a digest cycle, execute the upload response function in the active scope
                        // else execute the upload response function in the current digest
                        if (normalize && noErrors) {
                            if (angular.isDefined(content.entities)) {
                                modelsUtil.normalizeMultiple(content.entities);
                            } else if (angular.isDefined(content.entity)) {
                                modelsUtil.normalize(content.entity);
                            }
                        }
                        if (noErrors) {
                            if (!scope.$$phase) {
                                scope.$apply(function () {
                                    fn(scope, response);
                                });
                            } else {
                                fn(scope, response);
                            }
                        } else {
                            if (!scope.$$phase) {
                                scope.$apply(function () {
                                    errorFn(scope, response);
                                });
                            } else {
                                errorFn(scope, response);
                            }
                        }



                        $rootScope.$broadcast('disableUI', false);

                        if (noErrors) {
                            scope.$broadcast('ngUploadComplete', content);
                        } else {
                            errorHandling.modal(content.errors);
                            scope.$broadcast('ngUploadCompleteError', content);
                        }


                    }
                }
            };
        }
    ]);
