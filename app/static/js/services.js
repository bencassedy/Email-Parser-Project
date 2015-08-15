esApp.factory('TagService', function() {
	var sharedTags = {};
	return sharedTags;
});

esApp.factory('ResultService', function() {
	var sharedResults = {};
	return sharedResults;
});

    // $scope.getSelectedTags = function() {
    //     $scope.selectedTags = $filter('filter')($scope.tags, {selected: true});
    //     $scope.selectedTagNames = [];
    //     angular.forEach($scope.selectedTags, function(tag) {
    //         angular.forEach(tag, function(value, key) {
    //             if (key === 'name') {
    //                 $scope.selectedTagNames.push(" " + value);
    //             }
    //         });
    //     });
    // };
