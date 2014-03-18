esApp.controller('SearchCtrl', function($scope, es) {
    es.cluster.health(function (err, resp) {
        if (err) {
            $scope.data = err.message;
        } else {
            $scope.data = resp;
        }
    });

    $scope.fieldSelect = 'body';

    $scope.search = function() {
        es.search({
            index: 'test_kaminski',
            size: 50,
            body: {
                query: {
                    query_string: {
                        default_field: $scope.fieldSelect, 
                        query: ($scope.queryTerm || '*')
                    }
                }
            }
        }).then(function (resp) {
            $scope.results = resp.hits.hits;
            $scope.hitCount = resp.hits.total;
            }, function (err) {
                $scope.results(err.message);
        });
    };


    es.indices.getMapping({index:'test_kaminski', type:'email'}, function(err, resp) {
        if (err) {
            $scope.fields = err.message;
        } else {
            $scope.fields = Object.keys(resp.email.properties);
        }
    });


    $scope.multiSearchArray = [];
    $scope.multiSearchArrayResults = [];
    
    $scope.multisearch = function() {
        angular.forEach($scope.multiSearchArray, function(value) {
            es.count({
                index: 'test_kaminski',
                body: {
                    term: {
                        _all: value
                    }
                }
            }).then(function(resp) {
                $scope.multiSearchArrayResults.push({term: value, hits: resp.count});
            }, function(err) {
                $scope.multiSearchArrayResults.push({term: value, hits: err});
            });
        });
    };


    angular.element(document).ready(function () {
      $scope.search();
    });

    $scope.predicate = '';
});

esApp.controller('TagCtrl', function($scope, $http, $window) {
    $scope.tags = [
        "Responsive",
        "Non-Responsive",
        "Privileged",
        "Non-Privileged"
    ];

    $scope.addTag = function() {
        $http
            .post('/add_tag', {
                name: $scope.tagValue
            })
            .success(function(data, status, headers, config) {
                if (data.success) {
                    $scope.tagSuccess = true;
                } else {
                    $window.alert('Adding of tag failed');
                }
            })
            .error(function(data, status, headers, config) {
            });

        $scope.tags.push($scope.tagValue);
        $scope.tagValue = '';
    }
});
