angular.module('app.ui',
	  [
	   'app.ui.transition', 
	   'app.ui.collapse', 
	   'app.ui.accordion'
	  ]
);

angular.module('TestApp', ['app.ui'], function($httpProvider){
});

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