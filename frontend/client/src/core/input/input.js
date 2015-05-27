(function () {

    angular.module('material.components.input', [
            'material.core'
        ])
        .directive('mdInputContainer', mdInputContainerDirective)
        .directive('label', labelDirective)
        .directive('input', inputTextareaDirective)
        .directive('textarea', inputTextareaDirective)
        .directive('mdMaxlength', mdMaxlengthDirective)
        .directive('placeholder', placeholderDirective);

    function mdInputContainerDirective($parse) {
        ContainerCtrl.$inject = ["$scope", "$element", "$attrs"];
        return {
            restrict: 'E',
            link: postLink,
            controller: ContainerCtrl
        };

        function postLink(scope, element, attr) {

        }

        function ContainerCtrl($scope, $element, $attrs) {
            var self = this;

            self.isErrorGetter = $attrs.mdIsError && $parse($attrs.mdIsError);

            self.element = $element;
            self.setFocused = function (isFocused) {
                $element.toggleClass('md-input-focused', !!isFocused);
            };
            self.setHasValue = function (hasValue) {
                $element.toggleClass('md-input-has-value', !!hasValue);
            };
            self.setNoFloat = function (hasValue) {
                $element.toggleClass('md-input-no-float', !!hasValue);
            };
            self.setInvalid = function (isInvalid) {
                $element.toggleClass('md-input-invalid', !!isInvalid);
            };
            $scope.$watch(function () {
                return self.label && self.input;
            }, function (hasLabelAndInput) {
                if (hasLabelAndInput && !self.label.attr('for')) {
                    self.label.attr('for', self.input.attr('id'));
                }
            });
        }
    }
    mdInputContainerDirective.$inject = ["$parse"];

    function labelDirective() {
        return {
            restrict: 'E',
            require: '^?mdInputContainer',
            link: function (scope, element, attr, containerCtrl) {
                if (!containerCtrl) return;

                containerCtrl.label = element;
                scope.$on('$destroy', function () {
                    containerCtrl.label = null;
                });
            }
        };
    }

    function inputTextareaDirective($mdUtil, $window, $compile, $animate) {
        return {
            restrict: 'E',
            require: ['^?mdInputContainer', '?ngModel'],
            link: postLink
        };

        function postLink(scope, element, attr, ctrls) {

            var containerCtrl = ctrls[0];
            var ngModelCtrl = ctrls[1] || $mdUtil.fakeNgModel();
            var isReadonly = angular.isDefined(attr.readonly);

            if (!containerCtrl) return;
            if (containerCtrl.input) {
                throw new Error("<md-input-container> can only have *one* <input> or <textarea> child element!");
            }
            containerCtrl.input = element;

            element.addClass('md-input');
            if (!element.attr('id')) {
                element.attr('id', 'input_' + $mdUtil.nextUid());
            }

            function ngModelPipelineCheckValue(arg) {
                containerCtrl.setHasValue(!ngModelCtrl.$isEmpty(arg));
                return arg;
            }

            function inputCheckValue() {
                // An input's value counts if its length > 0,
                // or if the input's validity state says it has bad input (eg string in a number input)
                containerCtrl.setHasValue(element.val().length > 0 || (element[0].validity || {}).badInput);
            }


            var isErrorGetter = containerCtrl.isErrorGetter || function () {
                return ngModelCtrl.$invalid && (ngModelCtrl.$dirty || ngModelCtrl.$touched);
            };
            scope.$watch(isErrorGetter, containerCtrl.setInvalid);

            ngModelCtrl.$parsers.push(ngModelPipelineCheckValue);
            ngModelCtrl.$formatters.push(ngModelPipelineCheckValue);

            element.on('input', inputCheckValue);

            if (!isReadonly) {
                element
                    .on('focus', function (ev) {
                        containerCtrl.setFocused(true);
                    })
                    .on('blur', function (ev) {
                        containerCtrl.setFocused(false);
                        inputCheckValue();
                    });
            }

            scope.$on('$destroy', function () {
                containerCtrl.setFocused(false);
                containerCtrl.setHasValue(false);
                containerCtrl.input = null;
            });
        }
    }
    inputTextareaDirective.$inject = ["$mdUtil", "$window", "$compile", "$animate"];

    function mdMaxlengthDirective($animate) {
        return {
            restrict: 'A',
            require: ['ngModel', '^mdInputContainer'],
            link: postLink
        };

        function postLink(scope, element, attr, ctrls) {
            var maxlength;
            var ngModelCtrl = ctrls[0];
            var containerCtrl = ctrls[1];
            var charCountEl = angular.element('<div class="md-char-counter">');

            // Stop model from trimming. This makes it so whitespace 
            // over the maxlength still counts as invalid.
            attr.$set('ngTrim', 'false');
            containerCtrl.element.append(charCountEl);

            ngModelCtrl.$formatters.push(renderCharCount);
            ngModelCtrl.$viewChangeListeners.push(renderCharCount);
            element.on('input keydown', function () {
                renderCharCount(); //make sure it's called with no args
            });

            scope.$watch(attr.mdMaxlength, function (value) {
                maxlength = value;
                if (angular.isNumber(value) && value > 0) {
                    if (!charCountEl.parent().length) {
                        $animate.enter(charCountEl, containerCtrl.element,
                            angular.element(containerCtrl.element[0].lastElementChild));
                    }
                    renderCharCount();
                } else {
                    $animate.leave(charCountEl);
                }
            });

            ngModelCtrl.$validators['md-maxlength'] = function (modelValue, viewValue) {
                if (!angular.isNumber(maxlength) || maxlength < 0) {
                    return true;
                }
                return (modelValue || element.val() || viewValue || '').length <= maxlength;
            };

            function renderCharCount(value) {
                charCountEl.text((element.val() || value || '').length + '/' + maxlength);
                return value;
            }
        }
    }
    mdMaxlengthDirective.$inject = ["$animate"];

    function placeholderDirective() {
        return {
            restrict: 'A',
            require: '^^?mdInputContainer',
            link: postLink
        };

        function postLink(scope, element, attr, inputContainer) {
            if (!inputContainer || element[0].hasAttribute('native-placeholder')) return;

            var placeholderText = attr.placeholder;
            element.removeAttr('placeholder');
            inputContainer.element.append('<div class="md-placeholder">' + placeholderText + '</div>');
        }
    }

})();
