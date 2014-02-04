ngtemplate_path = 'js/lib/angular/ui/';
angular.module('app.ui',
	  [
	   'app.ui.transition', 
	   'app.ui.collapse', 
	   'app.ui.accordion',
	   'app.ui.modal',
	   'app.ui.selection',
	  ]
);

angular.module('TestApp', ['app.ui']);

function AccordionDemoCtrl($scope) {
	
  $scope.oneAtATime = true;
  $scope.isopen = true;

  $scope.groups = [
    {
      title: "Dynamic Group Header - 1",
      content: "Dynamic Group Body - 1",
      isOpen : true,
    },
    {
      title: "Dynamic Group Header - 2",
      content: "Dynamic Group Body - 2"
    },
    {
      title: "Dynamic Group Header - 3",
      content: "Dynamic Group Body - 3"
    }
  ];

  $scope.items = ['Item 1', 'Item 2', 'Item 3'];

  $scope.addItem = function() {
    var newItemNo = $scope.items.length + 1;
    $scope.items.push('Item ' + newItemNo);
  };
}


var ModalDemoCtrl = function ($scope, $modal, $log) {

  $scope.items = ['item1', 'item2', 'item3'];

  $scope.open = function () {

    var modalInstance = $modal.open({
      templateUrl: 'myModalContent.html',
      controller: ModalInstanceCtrl,
      resolve: {
        items: function () {
          return $scope.items;
        }
      }
    });

    modalInstance.result.then(function (selectedItem) {
      $scope.selected = selectedItem;
    }, function () {
      $log.info('Modal dismissed at: ' + new Date());
    });
  };
};

// Please note that $modalInstance represents a modal window (instance) dependency.
// It is not the same as the $modal service used above.

var ModalInstanceCtrl = function ($scope, $modalInstance, items) {

  $scope.items = items;
  $scope.selected = {
    item: $scope.items[0]
  };

  $scope.ok = function () {
    $modalInstance.close($scope.selected.item);
  };

  $scope.cancel = function () {
    $modalInstance.dismiss('cancel');
  };
};