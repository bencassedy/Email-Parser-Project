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

    angular.element(document).ready(function () {
      $scope.search();
    });

    $scope.predicate = '';
});