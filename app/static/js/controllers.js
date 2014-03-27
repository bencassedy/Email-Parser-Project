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
            size: 200,
            suggestText: ($scope.queryTerm || ''),
            body: {
                query: {
                    query_string: {
                        default_field: $scope.fieldSelect, 
                        query: ($scope.queryTerm || '*')
                    }
                },
                highlight: {
                    pre_tags: ["<mark>"],
                    post_tags: ["</mark>"],
                    fields: {
                        body: {}
                    }
                }
            }
        }).then(function (resp) {
            $scope.results = resp.hits.hits;
            $scope.hitCount = resp.hits.total;
            }, function (err) {
                $scope.results(err.message);
        });
        es.suggest({
            index: 'test_kaminski',
            suggestMode: 'popular',
            body: {
                mysuggester: {
                    text: ($scope.queryTerm || ''),
                    term: {
                        field: 'body',
                        suggest_mode: 'always'
                    }
                }
            }
        }).then(function(response) {
            $scope.suggestResults = response;
        }, function(error) {
            $scope.suggestResults = error.message;
        })
    };

    // $scope.toggleSuggester = function() {
    //     if ($scope.queryTerm == '') {
    //         $('p').hide();
    //     } else {
    //         $('p').show();
    //     }
    // };

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

esApp.controller('TagCtrl', ['$scope', '$http', '$window', '$filter', function($scope, $http, $window, $filter) {

    $scope.getTags = function() {
        $http
            .get('/tags')
            .success(function(data, status) {
                $scope.tags = data;
                $scope.status = status;
            })
            .error(function(data, status) {
                $scope.tags = data || "Request failed";
                $scope.status = status;
            });
        return $scope.tags;
    };

    $scope.addTag = function() {
        $http
            .post('/tags', {
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

        $scope.tags.push({name: $scope.tagValue});
        $scope.tagValue = '';
        return $scope.tags;
    };
    
    $scope.getSelectedTags = function() {
        $scope.selectedTags = $filter('filter')($scope.tags, {selected: true});
        $scope.selectedTagNames = [];
        angular.forEach($scope.selectedTags, function(tag) {
            angular.forEach(tag, function(value, key) {
                if (key === 'name') {
                    $scope.selectedTagNames.push(" " + value);
                }
            });
        });
    };


    $scope.deleteMessage = "Are you sure you want to delete the following tags? ";
    
    $scope.deleteTags = function(deleteMessage) {
        $scope.getSelectedTags();
        var okDelete = $window.confirm($scope.deleteMessage + $scope.selectedTagNames);
        if (okDelete) {
            $http
                .post('/tags_delete', $scope.selectedTags)
                .success(function(data, status, headers, config) {
                    if (data.success) {
                        $window.alert("Deletion of tags succeeded");
                        $scope.getTags();
                    } else {
                        $window.alert("Deletion of tags failed");
                    }
                })
                .error(function(data, status, headers, config) {

            });
        };
    };
}]);
